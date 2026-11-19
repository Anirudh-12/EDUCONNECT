package com.educonnect.app.data.local

import androidx.room.ColumnInfo
import androidx.room.Entity
import androidx.room.PrimaryKey

/**
 * Persistent sync outbox entity matching Section 6 of SYNC_PROTOCOL.md.
 */
@Entity(tableName = "sync_outbox")
data class SyncOutboxEntity(
    @PrimaryKey
    @ColumnInfo(name = "event_id")
    val eventId: String,

    @ColumnInfo(name = "event_type")
    val eventType: String,

    @ColumnInfo(name = "schema_version")
    val schemaVersion: Int,

    @ColumnInfo(name = "payload_json")
    val payloadJson: String,

    @ColumnInfo(name = "device_sequence")
    val deviceSequence: Int,

    @ColumnInfo(name = "created_at")
    val createdAt: String,

    @ColumnInfo(name = "status")
    val status: String = "pending", // pending, in_flight, acknowledged, rejected, requires_review

    @ColumnInfo(name = "retry_count")
    val retryCount: Int = 0,

    @ColumnInfo(name = "last_attempt_at")
    val lastAttemptAt: String? = null,

    @ColumnInfo(name = "acknowledged_at")
    val acknowledgedAt: String? = null
)
