import 'package:starter_architecture_flutter_firebase/src/common_widgets/delete_swipe_background.dart';
import 'package:starter_architecture_flutter_firebase/src/constants/breakpoints.dart';
import 'package:starter_architecture_flutter_firebase/src/localization/string_hardcoded.dart';
import 'package:starter_architecture_flutter_firebase/src/features/jobs/presentation/jobs_screen/job_card.dart';
import 'package:starter_architecture_flutter_firebase/src/common_widgets/responsive_center.dart';
import 'package:firebase_ui_firestore/firebase_ui_firestore.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:starter_architecture_flutter_firebase/src/constants/strings.dart';
import 'package:starter_architecture_flutter_firebase/src/features/jobs/data/jobs_repository.dart';
import 'package:starter_architecture_flutter_firebase/src/features/jobs/domain/job.dart';
import 'package:starter_architecture_flutter_firebase/src/features/jobs/presentation/jobs_screen/jobs_screen_controller.dart';
import 'package:starter_architecture_flutter_firebase/src/routing/app_router.dart';
import 'package:starter_architecture_flutter_firebase/src/utils/async_value_ui.dart';

class JobsScreen extends StatelessWidget {
  const JobsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    void addJob() => context.goNamed(AppRoute.addJob.name);
    return Scaffold(
      appBar: AppBar(title: const Text(Strings.jobs)),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: addJob,
        icon: const Icon(Icons.add),
        label: Text('New job'.hardcoded),
      ),
      body: Consumer(
        builder: (context, ref, child) {
          ref.listen<AsyncValue>(
            jobsScreenControllerProvider,
            (_, state) => state.showAlertDialogOnError(context),
          );
          final jobsQuery = ref.watch(jobsQueryProvider);
          return ResponsiveCenter(
            maxContentWidth: Breakpoint.content,
            child: FirestoreListView<Job>(
              query: jobsQuery,
              padding: const EdgeInsets.fromLTRB(16, 8, 16, 96),
              emptyBuilder: (context) => JobsEmptyState(onAdd: addJob),
              errorBuilder: (context, error, stackTrace) => Center(
                child: Text(error.toString()),
              ),
              loadingBuilder: (context) =>
                  const Center(child: CircularProgressIndicator()),
              itemBuilder: (context, doc) {
                final job = doc.data();
                return Padding(
                  padding: const EdgeInsets.only(bottom: 12),
                  child: Dismissible(
                    key: Key('job-${job.id}'),
                    background: const DeleteSwipeBackground(),
                    direction: DismissDirection.endToStart,
                    confirmDismiss: (_) => confirmJobDelete(context, job),
                    onDismissed: (direction) => ref
                        .read(jobsScreenControllerProvider.notifier)
                        .deleteJob(job),
                    child: JobCard(
                      job: job,
                      onTap: () => context.goNamed(
                        AppRoute.job.name,
                        pathParameters: {'id': job.id},
                      ),
                    ),
                  ),
                );
              },
            ),
          );
        },
      ),
    );
  }
}
