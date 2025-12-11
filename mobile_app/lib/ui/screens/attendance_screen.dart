import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import 'package:drift/drift.dart' as drift;
import 'dart:convert';
import '../../services/sync_service.dart';
import '../../data/database/database.dart';

class AttendanceScreen extends ConsumerStatefulWidget {
  const AttendanceScreen({super.key});

  @override
  ConsumerState<AttendanceScreen> createState() => _AttendanceScreenState();
}

class _AttendanceScreenState extends ConsumerState<AttendanceScreen> {
  Circle? _selectedCircle;
  DateTime _selectedDate = DateTime.now();

  @override
  Widget build(BuildContext context) {
    final db = ref.watch(databaseProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('تسجيل الحضور')),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(16.0),
            child: Row(
              children: [
                Expanded(
                  child: StreamBuilder<List<Circle>>(
                    stream: db.select(db.circles).watch(),
                    builder: (context, snapshot) {
                      if (!snapshot.hasData) return const LinearProgressIndicator();
                      final circles = snapshot.data!;
                      return DropdownButtonFormField<Circle>(
                        value: _selectedCircle,
                        hint: const Text('اختر الحلقة'),
                        items: circles.map((c) => DropdownMenuItem(value: c, child: Text(c.name))).toList(),
                        onChanged: (val) => setState(() => _selectedCircle = val),
                      );
                    },
                  ),
                ),
                IconButton(
                  icon: const Icon(Icons.calendar_today),
                  onPressed: () async {
                    final date = await showDatePicker(
                      context: context,
                      initialDate: _selectedDate,
                      firstDate: DateTime(2020),
                      lastDate: DateTime.now(),
                    );
                    if (date != null) setState(() => _selectedDate = date);
                  },
                ),
              ],
            ),
          ),
          if (_selectedCircle != null)
            Expanded(
              child: StreamBuilder<List<Student>>(
                stream: (db.select(db.students)..where((t) => t.circleId.equals(_selectedCircle!.id))).watch(),
                builder: (context, snapshot) {
                  if (!snapshot.hasData) return const Center(child: CircularProgressIndicator());
                  final students = snapshot.data!;

                  return ListView.builder(
                    itemCount: students.length,
                    itemBuilder: (context, index) {
                      final student = students[index];
                      // Fetch existing attendance
                      return _AttendanceRow(
                        student: student,
                        date: _selectedDate,
                        db: db,
                        ref: ref,
                      );
                    },
                  );
                },
              ),
            ),
        ],
      ),
    );
  }
}

class _AttendanceRow extends StatefulWidget {
  final Student student;
  final DateTime date;
  final AppDatabase db;
  final WidgetRef ref;

  const _AttendanceRow({
    required this.student,
    required this.date,
    required this.db,
    required this.ref,
  });

  @override
  State<_AttendanceRow> createState() => _AttendanceRowState();
}

class _AttendanceRowState extends State<_AttendanceRow> {
  String _status = 'حاضر';

  @override
  void initState() {
    super.initState();
    _loadStatus();
  }

  // Reload status when date changes
  @override
  void didUpdateWidget(covariant _AttendanceRow oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.date != widget.date) {
      _loadStatus();
    }
  }

  Future<void> _loadStatus() async {
    // Check local DB for attendance on this date
    final attendance = await (widget.db.select(widget.db.attendance)
      ..where((tbl) => tbl.studentId.equals(widget.student.id))
      ..where((tbl) => tbl.date.equals(widget.date))
    ).getSingleOrNull();

    if (attendance != null) {
      setState(() => _status = attendance.status);
    } else {
      setState(() => _status = 'حاضر'); // Default
    }
  }

  Future<void> _updateStatus(String? newStatus) async {
    if (newStatus == null) return;
    setState(() => _status = newStatus);

    // Save locally
    final entry = AttendanceCompanion(
      studentId: drift.Value(widget.student.id),
      date: drift.Value(widget.date),
      status: drift.Value(newStatus),
    );

    // Check if exists
    final existing = await (widget.db.select(widget.db.attendance)
      ..where((tbl) => tbl.studentId.equals(widget.student.id))
      ..where((tbl) => tbl.date.equals(widget.date))
    ).getSingleOrNull();

    if (existing != null) {
      await (widget.db.update(widget.db.attendance)..where((tbl) => tbl.id.equals(existing.id))).write(entry);
    } else {
      await widget.db.into(widget.db.attendance).insert(entry);
    }

    // Add to Sync Queue
    final payload = {
      'student_id': widget.student.id,
      'date': DateFormat('yyyy-MM-dd').format(widget.date),
      'status': newStatus,
    };

    await widget.db.into(widget.db.syncQueue).insert(SyncQueueCompanion(
      action: const drift.Value('INSERT'), // Simple insert for backend to handle upsert
      table: const drift.Value('attendance'),
      payload: drift.Value(jsonEncode(payload)),
    ));

    // Trigger sync
    widget.ref.read(syncServiceProvider).syncPush();
  }

  @override
  Widget build(BuildContext context) {
    return Card(
      child: ListTile(
        title: Text(widget.student.name),
        subtitle: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Radio<String>(value: 'حاضر', groupValue: _status, onChanged: _updateStatus),
            const Text('حاضر'),
            Radio<String>(value: 'غائب', groupValue: _status, onChanged: _updateStatus),
            const Text('غائب'),
          ],
        ),
      ),
    );
  }
}
