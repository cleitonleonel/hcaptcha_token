import json
import asyncio
import configparser
from flask import request, Flask, \
    render_template, jsonify, redirect
from playwright.async_api import Playwright, \
    async_playwright, expect

config = configparser.ConfigParser()
config.read('settings/config.ini', encoding="utf-8")

app = Flask(__name__)

token = None
host = config.get("server", "host")
port = config.get("server", "port")
site_key = config.get("hcaptcha", "site_key")
company_name = config.get("app", "company_name")
API_ALLOWED_IPS = json.loads(config.get("app", "allowed_ips"))


@app.route("/", methods=['GET'])
def index():
    return redirect("/hcaptcha")


@app.route("/hcaptcha", methods=['GET'])
def get_hcaptcha():
    ip_addr = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
    if ip_addr not in API_ALLOWED_IPS:
        return redirect("https://t.me/cleitonLC")
    return render_template('hcaptcha.html',
                           request={"company_name": company_name, "site_key": site_key})


@app.route("/success", methods=['GET'])
def success():
    return render_template('success.html',
                           request={"company_name": company_name})


@app.route('/hcaptcha/token', methods=['GET'])
def login():
    async def run(playwright: Playwright) -> None:
        global token
        browser = await playwright.firefox.launch(
            args=['--disable-blink-features=AutomationControlled'],
            headless=True
        )
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto(f"http://{host}:{port}/hcaptcha", wait_until='domcontentloaded')
        await page.frame_locator("center iframe").locator("div[role=\"checkbox\"]").click()
        token = await page.locator('#textarea').text_content()
        while True:
            await asyncio.sleep(0.01)
            break

        await browser.close()

    async def main() -> None:
        async with async_playwright() as playwright:
            await run(playwright)

    asyncio.run(main())
    # print(token)
    return jsonify(token)


app.run(host="0.0.0.0",
        port=9001,
        debug=True)
