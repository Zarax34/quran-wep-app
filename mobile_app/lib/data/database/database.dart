import 'package:drift/drift.dart';
import 'dart:io';
import 'package:drift/native.dart';
import 'package:path_provider/path_provider.dart';
import 'package:path/path.dart' as p;

part 'database.g.dart';

// --- Tables ---

class SyncQueue extends Table {
  IntColumn get id => integer().autoIncrement()();
  TextColumn get action => text()(); // 'INSERT', 'UPDATE', 'DELETE'
  TextColumn get table => text()(); // 'reports', 'attendance'
  TextColumn get payload => text()(); // JSON string
  DateTimeColumn get createdAt => dateTime().withDefault(currentDateAndTime)();
}

class Users extends Table {
  IntColumn get id => integer()(); // Server ID
  TextColumn get username => text()();
  TextColumn get name => text()();
  TextColumn get role => text()();

  @override
  Set<Column> get primaryKey => {id};
}

class Students extends Table {
  IntColumn get id => integer()(); // Server ID
  TextColumn get name => text()();
  IntColumn get circleId => integer().nullable()();
  TextColumn get phone => text().nullable()();
  IntColumn get totalVerses => integer().withDefault(const Constant(0))();
  TextColumn get lastSurah => text().nullable()();
  IntColumn get lastAyah => integer().withDefault(const Constant(0))();

  @override
  Set<Column> get primaryKey => {id};
}

class Circles extends Table {
  IntColumn get id => integer()(); // Server ID
  TextColumn get name => text()();
  IntColumn get teacherId => integer().nullable()();
  TextColumn get category => text().nullable()();

  @override
  Set<Column> get primaryKey => {id};
}

class Reports extends Table {
  IntColumn get id => integer().autoIncrement()(); // Local ID
  IntColumn get serverId => integer().nullable()(); // Server ID (null if not synced)
  IntColumn get studentId => integer()();
  DateTimeColumn get date => dateTime()();
  TextColumn get surah => text()();
  IntColumn get fromVerse => integer()();
  IntColumn get toVerse => integer()();
  TextColumn get grade => text()(); // Excellent, V.Good, etc.
  TextColumn get type => text()(); // Hifz, Muraja'ah
  TextColumn get status => text().withDefault(const Constant('Pending'))(); // Pending, Synced
  TextColumn get notes => text().nullable()();
}

class Attendance extends Table {
  IntColumn get id => integer().autoIncrement()();
  IntColumn get studentId => integer()();
  DateTimeColumn get date => dateTime()();
  TextColumn get status => text()(); // Present, Absent, etc.
}

@DriftDatabase(tables: [SyncQueue, Users, Students, Circles, Reports, Attendance])
class AppDatabase extends _$AppDatabase {
  AppDatabase() : super(_openConnection());

  @override
  int get schemaVersion => 1;
}

LazyDatabase _openConnection() {
  return LazyDatabase(() async {
    final dbFolder = await getApplicationDocumentsDirectory();
    final file = File(p.join(dbFolder.path, 'db.sqlite'));
    return NativeDatabase.createInBackground(file);
  });
}
