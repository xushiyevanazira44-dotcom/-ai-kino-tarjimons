import os, uuid, subprocess, shutil, json
from pathlib import Path
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
from openai import OpenAI

ROOT=Path(__file__).parent
UPLOAD=ROOT/"uploads"; OUTPUT=ROOT/"outputs"
UPLOAD.mkdir(exist_ok=True); OUTPUT.mkdir(exist_ok=True)
app=Flask(__name__)
CORS(app, resources={r"/*":{"origins":"*"}})
app.config["MAX_CONTENT_LENGTH"]=2*1024*1024*1024

def run_ffmpeg(args):
    p=subprocess.run(["ffmpeg","-y"]+args,capture_output=True,text=True)
    if p.returncode: raise RuntimeError(p.stderr[-2500:])

@app.get("/")
def root():
    return jsonify(ok=True,message="AI Kino Tarjimon API. Tekshirish uchun /health.")
@app.get("/health")
def health():
    return jsonify(ok=True,service="AI Kino Tarjimon API")
@app.post("/api/dub")
def dub():
    if not os.getenv("OPENAI_API_KEY"):
        return jsonify(error="Serverda OPENAI_API_KEY sozlanmagan."),500
    f=request.files.get("video")
    if not f or not f.filename: return jsonify(error="Video tanlanmagan."),400
    if not shutil.which("ffmpeg"): return jsonify(error="Serverda FFmpeg topilmadi."),500
    client=OpenAI()
    job=uuid.uuid4().hex[:10]
    ext=Path(secure_filename(f.filename)).suffix or ".mp4"
    src=UPLOAD/(job+ext); f.save(src)
    work=OUTPUT/job; work.mkdir()
    try:
        audio=work/"audio.mp3"
        run_ffmpeg(["-i",str(src),"-vn","-ac","1","-ar","16000","-b:a","64k",str(audio)])
        with open(audio,"rb") as af:
            transcript=client.audio.transcriptions.create(model="whisper-1",file=af,response_format="verbose_json",timestamp_granularities=["segment"])
        segments=transcript.segments or []
        if not segments: raise RuntimeError("Videoda aniqlanadigan nutq topilmadi.")
        translated=[]
        for offset in range(0,len(segments),8):
            group=segments[offset:offset+8]
            payload=[{"id":i,"text":s.text} for i,s in enumerate(group)]
            response=client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role":"system","content":"Translate each dialogue segment into natural spoken Uzbek in Latin script. Return JSON: {segments:[{id:number,text:string}]}."},
                    {"role":"user","content":json.dumps(payload,ensure_ascii=False)}
                ],
                response_format={"type":"json_object"}
            )
            rows=json.loads(response.choices[0].message.content).get("segments",[])
            mapping={int(x["id"]):x["text"] for x in rows if "id" in x and "text" in x}
            translated.extend(mapping.get(i,s.text) for i,s in enumerate(group))
        voice_files=[]
        for i,(seg,txt) in enumerate(zip(segments,translated)):
            raw=work/f"voice_{i:04d}.mp3"
            client.audio.speech.create(model="tts-1",voice="alloy",input=txt,response_format="mp3").stream_to_file(raw)
            delay=max(0,int(float(seg.start)*1000))
            duration=max(0.6,float(seg.end)-float(seg.start))
            fitted=work/f"fit_{i:04d}.mp3"
            run_ffmpeg(["-i",str(raw),"-af",f"apad,atrim=0:{duration:.3f},adelay={delay}|{delay}",str(fitted)])
            voice_files.append(fitted)
        output=OUTPUT/f"{job}_uzbek_dub.mp4"
        inputs=["-i",str(src)]
        for p in voice_files: inputs += ["-i",str(p)]
        labels="".join(f"[{i+1}:a]" for i in range(len(voice_files)))
        graph=f"[0:a]volume=0.18[original];{labels}amix=inputs={len(voice_files)}:duration=longest:normalize=0[uz];[original][uz]amix=inputs=2:duration=first:weights=0.25 1[aout]"
        run_ffmpeg(inputs+["-filter_complex",graph,"-map","0:v:0","-map","[aout]","-c:v","copy","-c:a","aac","-b:a","192k","-shortest",str(output)])
        return jsonify(download=f"/download/{output.name}",segments=len(segments))
    except Exception as e:
        return jsonify(error=str(e)),500
    finally:
        try: src.unlink()
        except OSError: pass

@app.get("/download/<name>")
def download(name):
    path=OUTPUT/secure_filename(name)
    if not path.exists(): return jsonify(error="Tayyor video topilmadi."),404
    return send_file(path,as_attachment=True,download_name=path.name)

if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.getenv("PORT","10000")))
