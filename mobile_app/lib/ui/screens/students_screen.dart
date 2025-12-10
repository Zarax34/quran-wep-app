import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../services/sync_service.dart';

class StudentsScreen extends ConsumerWidget {
  const StudentsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final db = ref.watch(databaseProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('الطلاب')),
      body: StreamBuilder(
        stream: db.select(db.students).watch(),
        builder: (context, snapshot) {
          if (snapshot.hasError) {
            return Center(child: Text('Error: ${snapshot.error}'));
          }
          if (!snapshot.hasData) {
            return const Center(child: CircularProgressIndicator());
          }

          final students = snapshot.data!;
          if (students.isEmpty) {
            return const Center(child: Text('لا يوجد طلاب'));
          }

          return ListView.builder(
            itemCount: students.length,
            itemBuilder: (context, index) {
              final student = students[index];
              return ListTile(
                leading: CircleAvatar(child: Text(student.name[0])),
                title: Text(student.name),
                subtitle: Text('آخر حفظ: ${student.lastSurah ?? "-"}'),
                trailing: const Icon(Icons.arrow_forward_ios, size: 16),
              );
            },
          );
        },
      ),
    );
  }
}
