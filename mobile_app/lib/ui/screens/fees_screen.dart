import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../services/sync_service.dart';
import '../../data/database/database.dart';

class FeesScreen extends ConsumerWidget {
  const FeesScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final db = ref.watch(databaseProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('الرسوم')),
      body: StreamBuilder(
        stream: db.select(db.fees).watch(),
        builder: (context, snapshot) {
          if (!snapshot.hasData) return const Center(child: CircularProgressIndicator());
          final fees = snapshot.data!;

          if (fees.isEmpty) return const Center(child: Text('لا توجد سجلات رسوم'));

          return ListView.builder(
            itemCount: fees.length,
            itemBuilder: (context, index) {
              final fee = fees[index];
              return Card(
                margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                child: ListTile(
                  title: Text(fee.title ?? 'رسوم'),
                  subtitle: Text('المبلغ: ${fee.amount}'),
                  trailing: Icon(
                    fee.status == 'Paid' ? Icons.check_circle : Icons.warning,
                    color: fee.status == 'Paid' ? Colors.green : Colors.orange,
                  ),
                ),
              );
            },
          );
        },
      ),
    );
  }
}
