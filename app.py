from flask import Flask, request, jsonify
from redis_config import redis_client
from datetime import datetime
import uuid #for generating unique Post IDs

app = Flask(__name__)

@app.route('/')
def home():
    return "🚀 Redis Social Media API is running!"

@app.route('/user', methods = ['POST'])
def add_user():
    data = request.get_json()
    user_id = data.get('user_id')
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400
    
    redis_client.hset(f"user:{user_id}", mapping=data)
    return jsonify({"message": "User added successfully"})

@app.route('/user/<user_id>', methods = ['GET'])
def get_user(user_id):
    user_data = redis_client.hgetall(f"user:{user_id}")
    if not user_data:
        return jsonify({"error": "User not found"}), 404
    return jsonify(user_data), 200

@app.route('/post', methods = ['POST'])
def create_post():
    data = request.get_json()
    user_id = data.get('user_id')
    content = data.get('content')

    if not user_id or not content:
        return jsonify({"error": "user_id and content are required"}), 400
    
    if not redis_client.exists(f"user:{user_id}"):
        return jsonify({"error": "User not found"}), 404
    
    post_id = str(uuid.uuid4())

    redis_client.hset(f"post:{post_id}", mapping = {
        "post_id": post_id,
        "user_id": user_id,
        "content": content,
        "timestamp": datetime.utcnow().isoformat()
    })

    redis_client.lpush(f"user:{user_id}:posts", post_id)

    return jsonify({"message": "Post created", "post_id": post_id}), 201


@app.route('/follow', methods = ['POST'])
def follow_user():
    data = request.get_json()
    follower_id = data.get('follower_id')
    followee_id = data.get('followee_id')

    if not follower_id or not followee_id:
        return jsonify({"error": "follower_id and followee_id are required"}), 400
    
    if not redis_client.exists(f"user:{follower_id}") or not redis_client.exists(f"user:{followee_id}"):
        return jsonify({"error": "User not found"}), 404
    
    #add followee_id to the follower's following set
    redis_client.sadd(f"user:{follower_id}:following", followee_id)

    #add follower_id to the followee's followers set
    redis_client.sadd(f"user:{followee_id}:followers", follower_id)

    return jsonify({"message": f"User {follower_id} is now following {followee_id}"}), 200

@app.route('/timeline/<user_id>', methods=['GET'])
def get_timeline(user_id):
    if not redis_client.exists(f"user:{user_id}"):
        return jsonify({"error": "User does not exists"}), 404
    
    timeline_posts = []

    #get list of user this user is following
    following_ids = redis_client.smembers(f"user:{user_id}:following")

    for followee_id in following_ids:
        #get recent post IDs for each folllowee
        post_ids = redis_client.lrange(f"user:{followee_id}:posts", 0, 4)

        for post_id in post_ids:
            post = redis_client.hgetall(f"post:{post_id}")
            if post:
                timeline_posts.append(post)

    #sort posts by timestamp in descending order
    sorted_posts = sorted(timeline_posts, key=lambda x: x['timestamp'], reverse=True)

    return jsonify(sorted_posts), 200

if __name__ == '__main__':
    app.run(debug=True)