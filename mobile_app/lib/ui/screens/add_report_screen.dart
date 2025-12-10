import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:drift/drift.dart' as drift;
import 'dart:convert';
import 'package:uuid/uuid.dart';
import '../../services/sync_service.dart';
import '../../data/database/database.dart';

class AddReportScreen extends ConsumerStatefulWidget {
  const AddReportScreen({super.key});

  @override
  ConsumerState<AddReportScreen> createState() => _AddReportScreenState();
}

class _AddReportScreenState extends ConsumerState<AddReportScreen> {
  final _formKey = GlobalKey<FormState>();
  Student? _selectedStudent;
  final _surahController = TextEditingController();
  final _fromController = TextEditingController();
  final _toController = TextEditingController();
  String _type = 'حفظ';
  String _grade = 'ممتاز';

  @override
  Widget build(BuildContext context) {
    final db = ref.watch(databaseProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('إضافة تقرير')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Form(
          key: _formKey,
          child: Column(
            children: [
              StreamBuilder(
                stream: db.select(db.students).watch(),
                builder: (context, snapshot) {
                  if (!snapshot.hasData) return const CircularProgressIndicator();
                  return DropdownButtonFormField<Student>(
                    value: _selectedStudent,
                    items: snapshot.data!.map((s) => DropdownMenuItem(value: s, child: Text(s.name))).toList(),
                    onChanged: (val) => setState(() => _selectedStudent = val),
                    decoration: const InputDecoration(labelText: 'الطالب'),
                    validator: (val) => val == null ? 'مطلوب' : null,
                  );
                },
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: _surahController,
                decoration: const InputDecoration(labelText: 'السورة'),
                validator: (val) => val!.isEmpty ? 'مطلوب' : null,
              ),
              const SizedBox(height: 16),
              Row(children: [
                Expanded(child: TextFormField(
                  controller: _fromController,
                  decoration: const InputDecoration(labelText: 'من آية'),
                  keyboardType: TextInputType.number,
                )),
                const SizedBox(width: 16),
                Expanded(child: TextFormField(
                  controller: _toController,
                  decoration: const InputDecoration(labelText: 'إلى آية'),
                  keyboardType: TextInputType.number,
                )),
              ]),
              const SizedBox(height: 16),
              DropdownButtonFormField<String>(
                value: _type,
                items: ['حفظ', 'مراجعة'].map((e) => DropdownMenuItem(value: e, child: Text(e))).toList(),
                onChanged: (val) => setState(() => _type = val!),
                decoration: const InputDecoration(labelText: 'النوع'),
              ),
              const SizedBox(height: 16),
              DropdownButtonFormField<String>(
                value: _grade,
                items: ['ممتاز', 'جيد جدا', 'جيد', 'مقبول'].map((e) => DropdownMenuItem(value: e, child: Text(e))).toList(),
                onChanged: (val) => setState(() => _grade = val!),
                decoration: const InputDecoration(labelText: 'التقدير'),
              ),
              const SizedBox(height: 32),
              ElevatedButton(
                onPressed: _submit,
                style: ElevatedButton.styleFrom(minimumSize: const Size(double.infinity, 50)),
                child: const Text('حفظ'),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Future<void> _submit() async {
    if (_formKey.currentState!.validate()) {
      final db = ref.read(databaseProvider);
      final uuid = const Uuid().v4();

      final report = ReportsCompanion(
        studentId: drift.Value(_selectedStudent!.id),
        date: drift.Value(DateTime.now()),
        surah: drift.Value(_surahController.text),
        fromVerse: drift.Value(int.parse(_fromController.text)),
        toVerse: drift.Value(int.parse(_toController.text)),
        type: drift.Value(_type),
        grade: drift.Value(_grade),
        status: const drift.Value('Pending'),
        uuid: drift.Value(uuid),
      );

      // Save locally
      await db.into(db.reports).insert(report);

      // Add to Sync Queue
      final payload = {
        'student_id': _selectedStudent!.id,
        'circle_id': _selectedStudent!.circleId,
        'date': DateTime.now().toIso8601String().substring(0, 10),
        'surah': _surahController.text,
        'from_verse': int.parse(_fromController.text),
        'to_verse': int.parse(_toController.text),
        'type': _type,
        'grade': _grade,
        'uuid': uuid,
      };

      await db.into(db.syncQueue).insert(SyncQueueCompanion(
        action: const drift.Value('INSERT'),
        table: const drift.Value('reports'),
        payload: drift.Value(jsonEncode(payload)),
      ));

      // Trigger sync if online (Optional, handled by background service usually)
      ref.read(syncServiceProvider).syncPush();

      if (mounted) Navigator.pop(context);
    }
  }
}
