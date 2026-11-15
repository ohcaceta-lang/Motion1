"""Diagnóstico da skill Google Flow: abre o Flow com o perfil salvo, lista os botões e tira um print.
Não gera nada nem gasta créditos. Uso (na pasta da skill):  python diag.py
Se aparecer "add Proyecto nuevo" no fim da lista, login e idioma estão OK.
"""
import asyncio
from playwright.async_api import async_playwright
from flow_provider import settings


async def main():
    async with async_playwright() as p:
        ctx = await p.chromium.launch_persistent_context(
            user_data_dir=str(settings.FLOW_CHROME_PROFILE),
            headless=False, channel="chrome",
            args=["--disable-blink-features=AutomationControlled", "--lang=es-419"],
            viewport={"width": 1280, "height": 900}, locale="es-419")
        page = ctx.pages[0] if ctx.pages else await ctx.new_page()
        await page.goto("https://flow.google.com/?hl=es-419")
        await page.wait_for_timeout(12000)
        print("URL:", page.url)
        print("TITULO:", await page.title())
        print("BOTOES:")
        for b in await page.get_by_role("button").all():
            try:
                t = (await b.inner_text()).strip().replace("\n", " ")
                if t:
                    print("  -", t[:60])
            except Exception:
                pass
        await page.screenshot(path="diag.png")
        print("Print salvo em diag.png")
        await ctx.close()

asyncio.run(main())
