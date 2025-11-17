/*
 Navicat Premium Data Transfer

 Source Server         : localhost_27017
 Source Server Type    : MongoDB
 Source Server Version : 80201
 Source Host           : localhost:27017
 Source Schema         : qianwen_logs

 Target Server Type    : MongoDB
 Target Server Version : 80201
 File Encoding         : 65001

 Date: 31/10/2025 20:38:11
*/


// ----------------------------
// Collection structure for api_logs
// ----------------------------
db.getCollection("api_logs").drop();
db.createCollection("api_logs");
db.getCollection("api_logs").createIndex({
    "user_id": NumberInt("1"),
    timestamp: NumberInt("-1")
}, {
    name: "user_id_1_timestamp_-1"
});
db.getCollection("api_logs").createIndex({
    "session_id": NumberInt("1"),
    timestamp: NumberInt("-1")
}, {
    name: "session_id_1_timestamp_-1"
});
db.getCollection("api_logs").createIndex({
    "log_type": NumberInt("1")
}, {
    name: "log_type_1"
});

// ----------------------------
// Documents of api_logs
// ----------------------------
