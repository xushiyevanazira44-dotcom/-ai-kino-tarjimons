# AI Kino Tarjimon — tuzatilgan versiya

## 1) Netlify frontend
- ZIP'ni oching.
- Netlify Drop orqali `index.html` va `netlify.toml` turgan papkani deploy qiling.
- Yangi sahifada endi **Render backend URL** maydoni va **Serverni tekshirish** tugmasi bor.
- Netlify saytining o'z URL manzilini backend maydoniga yozmang.

## 2) Render backend
- Barcha loyiha fayllarini GitHub repository'ga yuklang.
- Render → New → Web Service → repository'ni tanlang.
- Dockerfile orqali deploy qiling.
- Environment Variables'da `OPENAI_API_KEY` nomi bilan OpenAI API kalitini kiriting.
- Deploy tugagach `https://SIZNING-RENDER-URL/health` manzilini oching. `{"ok":true,...}` javobi chiqishi kerak.
- Shu Render URL'ni Netlify sahifasidagi backend maydoniga yozib, Serverni tekshirish tugmasini bosing.

## 3) Ishlatish
Server tekshiruvi muvaffaqiyatli bo'lsa, video tanlang va dublyajni boshlang.

## Eslatma
Bu prototipda API kaliti serverda turadi. OpenAI API ishlatilishi pullik bo'lishi mumkin. Katta videolar server xotirasi va ishlash vaqtiga bog'liq. Bu versiya personajlar ovozini alohida ajratmaydi. Netlify frontendni, Render esa Python/FFmpeg backendni host qiladi.
