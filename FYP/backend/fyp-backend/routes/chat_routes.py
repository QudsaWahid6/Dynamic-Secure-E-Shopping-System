from flask import Blueprint, request, jsonify, g
from auth import protected
from services.supabase_service import supabase_client

chat_bp = Blueprint("chat_bp", __name__)


def _is_blocked(a_id, b_id):
    """Returns True if either user has blocked the other."""
    res = (
        supabase_client.table("blocks")
        .select("id")
        .or_(
            f"and(blocker_id.eq.{a_id},blocked_id.eq.{b_id}),"
            f"and(blocker_id.eq.{b_id},blocked_id.eq.{a_id})"
        )
        .execute()
    )
    return len(res.data) > 0


def _who_blocked(a_id, b_id):
    """Returns the id of whoever did the blocking, or None."""
    res = (
        supabase_client.table("blocks")
        .select("blocker_id, blocked_id")
        .or_(
            f"and(blocker_id.eq.{a_id},blocked_id.eq.{b_id}),"
            f"and(blocker_id.eq.{b_id},blocked_id.eq.{a_id})"
        )
        .execute()
    )
    if not res.data:
        return None
    return res.data[0]["blocker_id"]


def _get_other_party(conversation):
    """Given a conversation row, returns (customer_id, owner_user_id)."""
    store_res = (
        supabase_client.table("stores")
        .select("user_id")
        .eq("id", conversation["store_id"])
        .execute()
    )
    owner_id = store_res.data[0]["user_id"] if store_res.data else None
    return conversation["customer_id"], owner_id


# ---------------------------------------------------------------------
# CONVERSATIONS
# ---------------------------------------------------------------------

@chat_bp.route("/chat/conversations", methods=["GET"])
@protected
def get_conversations():
    try:
        role = g.user.get("role")
        uid = g.user["id"]

        if role == "customer":
            res = (
                supabase_client.table("conversations")
                .select("*, stores(name, user_id)")
                .eq("customer_id", uid)
                .eq("customer_deleted", False)
                .order("created_at", desc=True)
                .execute()
            )
        elif role == "store_owner":
            store_res = supabase_client.table("stores").select("id").eq("user_id", uid).execute()
            store_ids = [s["id"] for s in store_res.data]
            if not store_ids:
                return jsonify({"success": True, "data": []})
            res = (
                supabase_client.table("conversations")
                .select("*, users:customer_id(name, profile_image_url), stores(name)")
                .in_("store_id", store_ids)
                .eq("owner_deleted", False)
                .order("created_at", desc=True)
                .execute()
            )
        else:
            return jsonify({"success": False, "message": "Unauthorized"}), 403

        # attach last message + unread count for each conversation
        conversations = res.data
        for c in conversations:
            msg_res = (
                supabase_client.table("messages")
                .select("content, created_at, sender_id, is_read")
                .eq("conversation_id", c["id"])
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )
            c["last_message"] = msg_res.data[0] if msg_res.data else None

            unread_res = (
                supabase_client.table("messages")
                .select("id", count="exact")
                .eq("conversation_id", c["id"])
                .eq("is_read", False)
                .neq("sender_id", uid)
                .execute()
            )
            c["unread_count"] = unread_res.count or 0

        return jsonify({"success": True, "data": conversations})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@chat_bp.route("/chat/conversations", methods=["POST"])
@protected
def start_conversation():
    try:
        if g.user.get("role") != "customer":
            return jsonify({"success": False, "message": "Only customers can start a chat"}), 403

        data = request.get_json() or {}
        store_id = data.get("store_id")
        if not store_id:
            return jsonify({"success": False, "message": "store_id required"}), 400

        store_res = supabase_client.table("stores").select("user_id").eq("id", store_id).execute()
        if not store_res.data:
            return jsonify({"success": False, "message": "Store not found"}), 404
        owner_id = store_res.data[0]["user_id"]

        if _is_blocked(g.user["id"], owner_id):
            blocker = _who_blocked(g.user["id"], owner_id)
            if blocker == owner_id:
                return jsonify({"success": False, "blocked": True, "message": "You are blocked"}), 403
            else:
                return jsonify({"success": False, "blocked": True, "message": "This functionality has been closed temporarily"}), 403

        existing = (
            supabase_client.table("conversations")
            .select("*")
            .eq("customer_id", g.user["id"])
            .eq("store_id", store_id)
            .execute()
        )
        if existing.data:
            convo = existing.data[0]
            if convo["customer_deleted"]:
                supabase_client.table("conversations").update({"customer_deleted": False}).eq("id", convo["id"]).execute()
            return jsonify({"success": True, "data": convo})

        new_res = supabase_client.table("conversations").insert({
            "customer_id": g.user["id"],
            "store_id": store_id,
        }).execute()
        return jsonify({"success": True, "data": new_res.data[0]})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@chat_bp.route("/chat/conversations/<conversation_id>", methods=["DELETE"])
@protected
def delete_conversation(conversation_id):
    try:
        convo_res = supabase_client.table("conversations").select("*").eq("id", conversation_id).execute()
        if not convo_res.data:
            return jsonify({"success": False, "message": "Conversation not found"}), 404
        convo = convo_res.data[0]

        if g.user.get("role") == "customer":
            if convo["customer_id"] != g.user["id"]:
                return jsonify({"success": False, "message": "Unauthorized"}), 403
            supabase_client.table("conversations").update({"customer_deleted": True}).eq("id", conversation_id).execute()
        else:
            supabase_client.table("conversations").update({"owner_deleted": True}).eq("id", conversation_id).execute()

        return jsonify({"success": True, "message": "Chat deleted"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ---------------------------------------------------------------------
# MESSAGES
# ---------------------------------------------------------------------

@chat_bp.route("/chat/conversations/<conversation_id>/messages", methods=["GET"])
@protected
def get_messages(conversation_id):
    try:
        convo_res = supabase_client.table("conversations").select("*").eq("id", conversation_id).execute()
        if not convo_res.data:
            return jsonify({"success": False, "message": "Conversation not found"}), 404
        convo = convo_res.data[0]

        customer_id, owner_id = _get_other_party(convo)
        uid = g.user["id"]
        if uid not in (customer_id, owner_id):
            return jsonify({"success": False, "message": "Unauthorized"}), 403

        msgs_res = (
            supabase_client.table("messages")
            .select("*")
            .eq("conversation_id", conversation_id)
            .order("created_at", desc=False)
            .execute()
        )

        # mark messages from the other person as read
        supabase_client.table("messages").update({"is_read": True}) \
            .eq("conversation_id", conversation_id) \
            .neq("sender_id", uid) \
            .eq("is_read", False) \
            .execute()

        return jsonify({"success": True, "data": msgs_res.data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@chat_bp.route("/chat/conversations/<conversation_id>/messages", methods=["POST"])
@protected
def send_message(conversation_id):
    try:
        data = request.get_json() or {}
        content = (data.get("content") or "").strip()
        if not content:
            return jsonify({"success": False, "message": "Message cannot be empty"}), 400

        convo_res = supabase_client.table("conversations").select("*").eq("id", conversation_id).execute()
        if not convo_res.data:
            return jsonify({"success": False, "message": "Conversation not found"}), 404
        convo = convo_res.data[0]

        customer_id, owner_id = _get_other_party(convo)
        uid = g.user["id"]
        if uid not in (customer_id, owner_id):
            return jsonify({"success": False, "message": "Unauthorized"}), 403

        other_id = owner_id if uid == customer_id else customer_id

        if _is_blocked(uid, other_id):
            blocker = _who_blocked(uid, other_id)
            if blocker == other_id:
                return jsonify({"success": False, "blocked": True, "message": "You are blocked"}), 403
            else:
                return jsonify({"success": False, "blocked": True, "message": "This functionality has been closed temporarily"}), 403

        # reopen conversation for either side if they had deleted it
        supabase_client.table("conversations").update({
            "customer_deleted": False,
            "owner_deleted": False,
        }).eq("id", conversation_id).execute()

        msg_res = supabase_client.table("messages").insert({
            "conversation_id": conversation_id,
            "sender_id": uid,
            "content": content,
        }).execute()

        return jsonify({"success": True, "data": msg_res.data[0]})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@chat_bp.route("/chat/unread-count", methods=["GET"])
@protected
def unread_count():
    try:
        uid = g.user["id"]
        role = g.user.get("role")

        if role == "customer":
            convo_res = supabase_client.table("conversations").select("id").eq("customer_id", uid).execute()
        elif role == "store_owner":
            store_res = supabase_client.table("stores").select("id").eq("user_id", uid).execute()
            store_ids = [s["id"] for s in store_res.data]
            if not store_ids:
                return jsonify({"success": True, "count": 0})
            convo_res = supabase_client.table("conversations").select("id").in_("store_id", store_ids).execute()
        else:
            return jsonify({"success": True, "count": 0})

        convo_ids = [c["id"] for c in convo_res.data]
        if not convo_ids:
            return jsonify({"success": True, "count": 0})

        msg_res = (
            supabase_client.table("messages")
            .select("id", count="exact")
            .in_("conversation_id", convo_ids)
            .eq("is_read", False)
            .neq("sender_id", uid)
            .execute()
        )
        return jsonify({"success": True, "count": msg_res.count or 0})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ---------------------------------------------------------------------
# BLOCKING
# ---------------------------------------------------------------------

@chat_bp.route("/chat/block", methods=["POST"])
@protected
def block_user():
    try:
        data = request.get_json() or {}
        blocked_id = data.get("user_id")
        if not blocked_id:
            return jsonify({"success": False, "message": "user_id required"}), 400
        if blocked_id == g.user["id"]:
            return jsonify({"success": False, "message": "Cannot block yourself"}), 400

        existing = (
            supabase_client.table("blocks")
            .select("id")
            .eq("blocker_id", g.user["id"])
            .eq("blocked_id", blocked_id)
            .execute()
        )
        if existing.data:
            return jsonify({"success": True, "message": "Already blocked"})

        supabase_client.table("blocks").insert({
            "blocker_id": g.user["id"],
            "blocked_id": blocked_id,
        }).execute()
        return jsonify({"success": True, "message": "User blocked"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@chat_bp.route("/chat/block/<blocked_id>", methods=["DELETE"])
@protected
def unblock_user(blocked_id):
    try:
        supabase_client.table("blocks").delete() \
            .eq("blocker_id", g.user["id"]) \
            .eq("blocked_id", blocked_id) \
            .execute()
        return jsonify({"success": True, "message": "User unblocked"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@chat_bp.route("/chat/blocked", methods=["GET"])
@protected
def list_blocked():
    try:
        res = (
            supabase_client.table("blocks")
            .select("id, blocked_id, created_at, users:blocked_id(name, email, profile_image_url)")
            .eq("blocker_id", g.user["id"])
            .execute()
        )
        return jsonify({"success": True, "data": res.data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500