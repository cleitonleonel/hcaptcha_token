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
    global token
    custom_headers = {
        "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                     'Chrome/83.0.4103.116 Safari/537.36'
    }

    async def run(playwright: Playwright) -> None:
        global token
        browser = await playwright.firefox.launch(
            args=["--disable-blink-features=AutomationControlled"],
            headless=False
        )
        context = await browser.new_context(proxy={"server": f"http://{host}:{port}"})
        page = await context.new_page()
        await context.set_extra_http_headers(headers=custom_headers)
        await page.goto(f"http://{host}:{port}/hcaptcha", wait_until='domcontentloaded')
        await page.frame_locator("center iframe").locator("div[role=\"checkbox\"]").click()
        token = await page.locator('#textarea').text_content()
        while True:
            await asyncio.sleep(2)
            break
        await page.close()
        await browser.close()

    async def main() -> None:
        async with async_playwright() as playwright:
            await run(playwright)

    try:
        asyncio.run(main())
    except:
        token = None

    return jsonify({"x-captcha-response": token})


app.run(host="0.0.0.0",
        port=9001,
        debug=True)
