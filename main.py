import asyncio
from pathlib import Path
import httpx

# PROJE 7 - Eszamanli Parcali Dosya Indirme
URL = "https://proof.ovh.net/files/1Mb.dat"
WORKERS = 4
OUTPUT = Path(__file__).with_name("indirilen_dosya.bin")


async def download():
    async with httpx.AsyncClient(
        timeout=60,
        follow_redirects=True
    ) as client:

        # 1. HEAD sorgusu
        head = await client.head(URL)
        head.raise_for_status()

        size = int(head.headers["Content-Length"])
        accept_ranges = head.headers.get(
            "Accept-Ranges", ""
        ).lower()

        print("Dosya boyutu:", size, "bayt")

        if accept_ranges != "bytes":
            raise RuntimeError(
                "Sunucu parcali indirmeyi desteklemiyor."
            )

        if size < WORKERS:
            raise RuntimeError("Dosya cok kucuk.")

        # 2. Bayt segmentasyonu
        ranges = [
            (
                i * size // WORKERS,
                (i + 1) * size // WORKERS - 1
            )
            for i in range(WORKERS)
        ]

        for i, (start, end) in enumerate(ranges):
            print(f"Parca {i+1}: {start}-{end}")

        # 3. Hedef dosyayi olustur
        with open(OUTPUT, "wb") as f:
            f.truncate(size)

        async def worker(index, start, end):
            headers = {
                "Range": f"bytes={start}-{end}"
            }

            async with client.stream(
                "GET", URL, headers=headers
            ) as response:

                if response.status_code != 206:
                    raise RuntimeError(
                        f"Parca {index+1}: HTTP 206 alinmadi."
                    )

                expected = f"bytes {start}-{end}/{size}"
                actual = response.headers.get(
                    "Content-Range", ""
                )

                if actual != expected:
                    raise RuntimeError(
                        "Content-Range hatali."
                    )

                # 4. Windows uyumlu ofset yazimi
                with open(OUTPUT, "r+b", buffering=0) as f:
                    f.seek(start)
                    position = start

                    async for chunk in response.aiter_bytes():
                        if position + len(chunk) > end + 1:
                            raise RuntimeError(
                                "Parca siniri asildi."
                            )

                        view = memoryview(chunk)

                        while len(view) > 0:
                            written = f.write(view)
                            if written is None or written <= 0:
                                raise OSError("Yazma hatasi.")
                            view = view[written:]

                        position += len(chunk)

                    if position != end + 1:
                        raise RuntimeError(
                            f"Parca {index+1} eksik."
                        )

            print(f"Parca {index+1} tamamlandi.")

        try:
            await asyncio.gather(
                *(
                    worker(i, start, end)
                    for i, (start, end) in enumerate(ranges)
                )
            )
        except Exception:
            OUTPUT.unlink(missing_ok=True)
            raise

        final_size = OUTPUT.stat().st_size

        if final_size != size:
            raise RuntimeError(
                "Dosya boyutu uyusmuyor."
            )

        print("Indirme basariyla tamamlandi!")
        print("Dosya:", OUTPUT.name)
        print("Toplam bayt:", final_size)


if __name__ == "__main__":
    asyncio.run(download())