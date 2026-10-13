import 'package:riverpod/riverpod.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';
import 'package:rxdart/rxdart.dart';
import 'package:starter_architecture_flutter_firebase/src/features/authentication/data/firebase_auth_repository.dart';
import 'package:starter_architecture_flutter_firebase/src/features/authentication/domain/app_user.dart';
import 'package:starter_architecture_flutter_firebase/src/features/entries/data/entries_repository.dart';
import 'package:starter_architecture_flutter_firebase/src/features/entries/domain/daily_jobs_details.dart';
import 'package:starter_architecture_flutter_firebase/src/features/entries/domain/timesheet.dart';
import 'package:starter_architecture_flutter_firebase/src/features/entries/domain/entry_job.dart';
import 'package:starter_architecture_flutter_firebase/src/features/jobs/data/jobs_repository.dart';
import 'package:starter_architecture_flutter_firebase/src/features/entries/domain/entry.dart';
import 'package:starter_architecture_flutter_firebase/src/features/jobs/domain/job.dart';

part 'entries_service.g.dart';

class EntriesService {
  EntriesService(
      {required this.jobsRepository, required this.entriesRepository});
  final JobsRepository jobsRepository;
  final EntriesRepository entriesRepository;

  /// Label for entries whose job no longer exists (deleted while the stream was catching up).
  static const deletedJobName = '(deleted job)';

  /// Pairs each entry with its job. An entry whose job is gone gets a placeholder job instead of throwing.
  static List<EntryJob> combine(List<Entry> entries, List<Job> jobs) {
    final byId = {for (final job in jobs) job.id: job};
    return [
      for (final entry in entries)
        EntryJob(entry, byId[entry.jobId] ?? Job(id: entry.jobId, name: deletedJobName, ratePerHour: 0)),
    ];
  }

  /// Groups the entries by day, newest first, with totals.
  static Timesheet timesheet(List<EntryJob> entries) {
    final days = DailyJobsDetails.all(entries)..sort((a, b) => b.date.compareTo(a.date));
    return Timesheet(
      days: days,
      totalHours: days.fold(0.0, (sum, d) => sum + d.duration),
      totalPay: days.fold(0.0, (sum, d) => sum + d.pay),
    );
  }

  Stream<Timesheet> timesheetStream(UserID uid) => CombineLatestStream.combine2(
        entriesRepository.watchEntries(uid: uid),
        jobsRepository.watchJobs(uid: uid),
        combine,
      ).map(timesheet);
}

@riverpod
EntriesService entriesService(Ref ref) {
  return EntriesService(
    jobsRepository: ref.watch(jobsRepositoryProvider),
    entriesRepository: ref.watch(entriesRepositoryProvider),
  );
}

@riverpod
Stream<Timesheet> timesheetStream(Ref ref) {
  final user = ref.watch(firebaseAuthProvider).currentUser;
  if (user == null) {
    throw AssertionError('User can\'t be null when fetching entries');
  }
  final entriesService = ref.watch(entriesServiceProvider);
  return entriesService.timesheetStream(user.uid);
}
