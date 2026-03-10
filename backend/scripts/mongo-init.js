// MongoDB initialization script
db = db.getSiblingDB('fatigue_prediction');

// Create collections
db.createCollection('users');
db.createCollection('devices');
db.createCollection('usage_data');
db.createCollection('notifications');
db.createCollection('qr_tokens');
db.createCollection('predictions');

// Create indexes
db.users.createIndex({ email: 1 }, { unique: true });
db.users.createIndex({ created_at: -1 });

db.devices.createIndex({ device_id: 1 }, { unique: true });
db.devices.createIndex({ user_id: 1 });
db.devices.createIndex({ pairing_status: 1 });

db.usage_data.createIndex({ user_id: 1, timestamp: -1 });
db.usage_data.createIndex({ device_id: 1, timestamp: -1 });
db.usage_data.createIndex({ timestamp: 1 }, { expireAfterSeconds: 2592000 }); // 30 days TTL

db.notifications.createIndex({ user_id: 1, created_at: -1 });
db.notifications.createIndex({ user_id: 1, read: 1 });

db.qr_tokens.createIndex({ token: 1 }, { unique: true });
db.qr_tokens.createIndex({ expires_at: 1 }, { expireAfterSeconds: 0 });

db.predictions.createIndex({ user_id: 1, timestamp: -1 });

print('✅ MongoDB initialized successfully');