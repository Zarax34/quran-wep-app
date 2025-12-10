import 'dart:convert';
import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:logger/logger.dart';
import 'package:drift/drift.dart' as drift;
import '../data/database/database.dart';
import 'api_service.dart';
import 'package:shared_preferences/shared_preferences.dart';

final syncServiceProvider = Provider((ref) => SyncService(
  ref.watch(databaseProvider),
  ref.watch(apiServiceProvider),
));

final databaseProvider = Provider<AppDatabase>((ref) => AppDatabase());
final apiServiceProvider = Provider<ApiService>((ref) => ApiService());

class SyncService {
  final AppDatabase db;
  final ApiService api;
  final Logger logger = Logger();

  SyncService(this.db, this.api);

  Future<void> syncPull() async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('auth_token');

    if (token == null) {
      logger.w("Cannot sync: No token");
      return;
    }

    try {
      final data = await api.fetchSyncData(token);

      await db.transaction(() async {
        // Sync Circles
        for (var c in data['circles']) {
          await db.into(db.circles).insertOnConflictUpdate(Circle(
            id: c['id'],
            name: c['name'],
            teacherId: c['teacher_id'],
            category: c['category'],
          ));
        }

        // Sync Students
        for (var s in data['students']) {
          await db.into(db.students).insertOnConflictUpdate(Student(
            id: s['id'],
            name: s['name'],
            circleId: s['circle_id'],
            phone: s['student_phone'],
            totalVerses: s['total_verses'] ?? 0,
            lastSurah: s['last_surah'],
            lastAyah: s['last_ayah'] ?? 0
          ));
        }

        // Sync Reports
        // The API returns 'reports' list. We should insert them.
        // We use insertOnConflictUpdate assuming 'id' from server is primary key.
        // However, our local Reports table has autoIncrement ID.
        // We need a serverId column to map them correctly.
        // If we get an ID from server, we check if we have a report with that serverId.

        if (data['reports'] != null) {
          for (var r in data['reports']) {
            // Check if exists by serverId
            final existing = await (db.select(db.reports)..where((tbl) => tbl.serverId.equals(r['id']))).getSingleOrNull();

            final report = ReportsCompanion(
              serverId: drift.Value(r['id']),
              studentId: drift.Value(r['student_id']),
              date: drift.Value(DateTime.parse(r['date'])),
              surah: drift.Value(r['surah']),
              fromVerse: drift.Value(r['from_verse'] ?? 0),
              toVerse: drift.Value(r['to_verse'] ?? 0),
              grade: drift.Value(r['grade']),
              type: drift.Value(r['type'] ?? 'حفظ'),
              status: drift.Value(r['status'] ?? 'Approved'),
            );

            if (existing != null) {
              // Update
              await (db.update(db.reports)..where((tbl) => tbl.serverId.equals(r['id']))).write(report);
            } else {
              // Insert
              await db.into(db.reports).insert(report);
            }
          }
        }
      });

      logger.i("Pull Sync Complete");
    } catch (e) {
      logger.e("Pull Sync Failed", error: e);
    }
  }

  Future<void> syncPush() async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('auth_token');

    if (token == null) return;

    final queue = await db.select(db.syncQueue).get();
    if (queue.isEmpty) return;

    List<Map<String, dynamic>> reportsToPush = [];
    List<Map<String, dynamic>> attendanceToPush = [];
    List<int> processedIds = [];

    for (var item in queue) {
      final payload = jsonDecode(item.payload);
      if (item.table == 'reports' && item.action == 'INSERT') {
        reportsToPush.add(payload);
        processedIds.add(item.id);
      } else if (item.table == 'attendance') {
        attendanceToPush.add(payload);
        processedIds.add(item.id);
      }
    }

    if (reportsToPush.isEmpty && attendanceToPush.isEmpty) return;

    try {
      await api.pushSyncData(token, {
        'reports': reportsToPush,
        'attendance': attendanceToPush
      });

      // Clear queue on success
      await (db.delete(db.syncQueue)..where((tbl) => tbl.id.isIn(processedIds))).go();
      logger.i("Push Sync Complete: ${processedIds.length} items");
    } catch (e) {
      logger.e("Push Sync Failed", error: e);
    }
  }
}
