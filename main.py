from flask import Flask, request, jsonify
from sif import vanilla_insert_links,metabase_insert_links, metabase_get_post_links,scrap, vanilla_get_post_links,vanilla_get_order_ids_cogs
from apscheduler.schedulers.background import BackgroundScheduler
import atexit

app = Flask(__name__)

@app.route("/insert/links", methods=["POST"])
def insert_links():
    data = request.get_json()
    links = data.get("links", [])
    result = vanilla_insert_links(links)
    return jsonify(result)

@app.route("/get/post-links", methods=["POST"])
def get_post_links():
    data = request.get_json()

    links = data.get("links", [])

    rows = vanilla_get_post_links(links)

    formatted = {
        row["link"]: {
            "likes": row.get("likes", 0),
            "comments": row.get("comments", 0),
            "views": row.get("views", 0),
            "shares": row.get("shares", 0),

            "updated_at": row.get("updated_at", 0)

        }
        for row in rows
    }

    return jsonify(formatted)

@app.route("/get/cogs", methods=["POST"])
def get_cogs():
    data = request.get_json()
    user_claims = data["user_claims"]
    all_order_ids = data["all_order_ids"]

    res=vanilla_get_order_ids_cogs(all_order_ids)
    oid = {str(i["order_id"]): i["cogs"] for i in res}
    oid['']=0
    for i in user_claims:
        i["cogs"]=0
        for j in i["order_ids"]:
            
            i["cogs"]+=oid[j]
    formatted = {
        i["user"]:i["cogs"]
        for i in user_claims
    }
    
    

    return jsonify(formatted)



if __name__ == "__main__":
    app.run(debug=True, port=5000, host="0.0.0.0")
