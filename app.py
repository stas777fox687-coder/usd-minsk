import os
import time
from flask import Flask, render_template, request, Response, redirect, jsonify, abort
from rates import get_rates, last_update, refresh, get_branches

app = Flask(__name__)

USER = "friends"
PASSWORD = os.environ.get("SITE_PASSWORD", "777")

# банки, у которых на myfin нет отделений в Минске
NO_BRANCHES = {"belinkasgrupp", "belswissbank"}


def get_mode():
    # buy: ты покупаешь USD (курс продажи банка, чем ниже, тем лучше)
    # sell: ты продаёшь USD (курс покупки банка, чем выше, тем лучше)
    mode = 'sell' if request.args.get('mode') == 'sell' else 'buy'
    field = 'buy' if mode == 'sell' else 'sell'
    return mode, field


@app.before_request
def check_auth():
    auth = request.authorization
    if not auth or auth.username != USER or auth.password != PASSWORD:
        return Response("Нужен пароль", 401,
                        {"WWW-Authenticate": 'Basic realm="Login"'})


@app.route('/')
def index():
    mode, field = get_mode()
    banks = [b for b in get_rates() if b.get(field)]
    banks.sort(key=lambda b: b[field], reverse=(mode == 'sell'))
    main = [b for b in banks if b['alias'] not in NO_BRANCHES]
    extra = [b for b in banks if b['alias'] in NO_BRANCHES]
    best = main[0][field]
    worst = main[-1][field]
    updated = time.strftime("%H:%M", time.localtime(last_update()))
    return render_template('index.html', banks=main, extra=extra, best=best,
                           worst=worst, mode=mode, field=field, updated=updated)


@app.route('/branches/<alias>')
def branches(alias):
    mode, field = get_mode()
    if alias not in {b['alias'] for b in get_rates()}:
        abort(404)
    try:
        items = [{"address": x["address"], "rate": x[field]}
                 for x in get_branches(alias) if x.get(field)]
    except Exception:
        return jsonify([]), 502
    items.sort(key=lambda x: x["rate"], reverse=(mode == 'sell'))
    return jsonify(items)


@app.route('/refresh')
def do_refresh():
    refresh()
    mode, _ = get_mode()
    return redirect('/?mode=' + mode)


if __name__ == '__main__':
    app.run(debug=False)