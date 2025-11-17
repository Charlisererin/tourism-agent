/*
 Navicat Premium Data Transfer

 Source Server         : localhost_27017
 Source Server Type    : MongoDB
 Source Server Version : 80201
 Source Host           : localhost:27017
 Source Schema         : qianwen_memory

 Target Server Type    : MongoDB
 Target Server Version : 80201
 File Encoding         : 65001

 Date: 31/10/2025 20:38:17
*/


// ----------------------------
// Collection structure for conversations
// ----------------------------
db.getCollection("conversations").drop();
db.createCollection("conversations");
db.getCollection("conversations").createIndex({
    "user_id": NumberInt("1"),
    "session_id": NumberInt("1"),
    timestamp: NumberInt("-1")
}, {
    name: "user_id_1_session_id_1_timestamp_-1"
});
db.getCollection("conversations").createIndex({
    timestamp: NumberInt("1")
}, {
    name: "timestamp_1",
    expireAfterSeconds: NumberInt("604800")
});

// ----------------------------
// Documents of conversations
// ----------------------------
