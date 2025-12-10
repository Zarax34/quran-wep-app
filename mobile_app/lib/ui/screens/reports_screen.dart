import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../services/sync_service.dart';
import '../../data/database/database.dart';
import 'add_report_screen.dart';

class ReportsScreen extends ConsumerWidget {
  const ReportsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final db = ref.watch(databaseProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('التقارير')),
      floatingActionButton: FloatingActionButton(
        onPressed: () {
          Navigator.push(context, MaterialPageRoute(builder: (_) => const AddReportScreen()));
        },
        child: const Icon(Icons.add),
      ),
      body: StreamBuilder(
        stream: db.select(db.reports).watch(),
        builder: (context, snapshot) {
          if (!snapshot.hasData) return const Center(child: CircularProgressIndicator());
          final reports = snapshot.data!;

          return ListView.builder(
            itemCount: reports.length,
            itemBuilder: (context, index) {
              final report = reports[index];
              return Card(
                margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                child: ListTile(
                  title: Text(report.surah),
                  subtitle: Text('${report.type} - ${report.grade}'),
                  trailing: Text(report.status,
                    style: TextStyle(color: report.status == 'Pending' ? Colors.orange : Colors.green)),
                ),
              );
            },
          );
        },
      ),
    );
  }
}
