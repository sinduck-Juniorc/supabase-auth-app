package org.zetamesh.ecotrekking.demo;

import org.json.JSONException;
import org.json.JSONObject;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;
import java.util.UUID;

final class OneHopLog {
    static final class Session {
        final String id = UUID.randomUUID().toString();
        int received, invalid, expired, repeatedOrOlder;
    }

    private final File file;

    OneHopLog(File directory) {
        file = new File(directory, "one-hop.jsonl");
    }

    boolean hasRecords() {
        return file.length() > 0;
    }

    void append(Session session, long elapsedMs, String event, Object... fields) throws IOException {
        try {
            JSONObject entry = new JSONObject();
            entry.put("schema_version", 1);
            entry.put("session_id", session.id);
            entry.put("event", event);
            entry.put("unix_ms", System.currentTimeMillis());
            entry.put("elapsed_ms", elapsedMs);
            for (int i = 0; i < fields.length; i += 2) {
                entry.put((String) fields[i], fields[i + 1]);
            }
            try (FileOutputStream out = new FileOutputStream(file, true)) {
                out.write((entry.toString() + "\n").getBytes(StandardCharsets.UTF_8));
            }
        } catch (JSONException error) {
            throw new IOException("JSON serialization failed", error);
        }
    }

    void export(OutputStream out) throws IOException {
        long remaining = file.length();
        if (remaining == 0) throw new IOException("No records to export");
        try (FileInputStream in = new FileInputStream(file)) {
            byte[] buffer = new byte[8192];
            while (remaining > 0) {
                int count = in.read(buffer, 0, (int) Math.min(buffer.length, remaining));
                if (count < 0) throw new IOException("Log ended unexpectedly");
                out.write(buffer, 0, count);
                remaining -= count;
            }
        }
    }
}
