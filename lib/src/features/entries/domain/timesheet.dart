import 'package:starter_architecture_flutter_firebase/src/features/entries/domain/daily_jobs_details.dart';

/// Everything the Entries tab shows: each day's hours and pay per job, newest day first, and the totals.
class Timesheet {
  const Timesheet({required this.days, required this.totalHours, required this.totalPay});
  final List<DailyJobsDetails> days;
  final double totalHours;
  final double totalPay;
}
