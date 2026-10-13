import 'package:starter_architecture_flutter_firebase/src/constants/breakpoints.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:starter_architecture_flutter_firebase/src/common_widgets/responsive_center.dart';
import 'package:starter_architecture_flutter_firebase/src/constants/app_sizes.dart';
import 'package:starter_architecture_flutter_firebase/src/features/entries/domain/entry.dart';
import 'package:starter_architecture_flutter_firebase/src/features/entries/domain/entry_times.dart';
import 'package:starter_architecture_flutter_firebase/src/features/entries/presentation/entry_screen/entry_editor.dart';
import 'package:starter_architecture_flutter_firebase/src/features/jobs/data/jobs_repository.dart';
import 'package:starter_architecture_flutter_firebase/src/features/jobs/domain/job.dart';
import 'package:starter_architecture_flutter_firebase/src/features/entries/presentation/entry_screen/entry_screen_controller.dart';
import 'package:starter_architecture_flutter_firebase/src/utils/async_value_ui.dart';

class EntryScreen extends ConsumerStatefulWidget {
  const EntryScreen({super.key, required this.jobId, this.entryId, this.entry});
  final JobID jobId;
  final EntryID? entryId;
  final Entry? entry;

  @override
  ConsumerState<EntryScreen> createState() => _EntryPageState();
}

class _EntryPageState extends ConsumerState<EntryScreen> {
  late EntryTimes _times;
  late String _comment;

  @override
  void initState() {
    super.initState();
    final entry = widget.entry;
    _times = entry == null ? EntryTimes.forNew(DateTime.now()) : EntryTimes.fromEntry(entry.start, entry.end);
    _comment = entry?.comment ?? '';
  }

  Future<void> _setEntryAndDismiss() async {
    final success =
        await ref.read(entryScreenControllerProvider.notifier).submit(
              entryId: widget.entryId,
              jobId: widget.jobId,
              start: _times.start,
              end: _times.end,
              comment: _comment,
            );
    if (success && mounted) {
      context.pop();
    }
  }

  @override
  Widget build(BuildContext context) {
    ref.listen<AsyncValue>(
      entryScreenControllerProvider,
      (_, state) => state.showAlertDialogOnError(context),
    );
    final isLoading = ref.watch(entryScreenControllerProvider).isLoading;
    final rate = ref.watch(jobStreamProvider(widget.jobId)).value?.ratePerHour ?? 0;
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.entry != null ? 'Edit entry' : 'New entry'),
        actions: <Widget>[
          Padding(
            padding: const EdgeInsets.only(right: 8),
            child: FilledButton(
              onPressed: isLoading ? null : _setEntryAndDismiss,
              child: Text(widget.entry != null ? 'Update' : 'Save'),
            ),
          ),
        ],
      ),
      body: SingleChildScrollView(
        child: ResponsiveCenter(
          maxContentWidth: Breakpoint.content,
          padding: const EdgeInsets.all(Sizes.p16),
          child: EntryEditor(
            times: _times,
            ratePerHour: rate,
            comment: _comment,
            onTimesChanged: (t) => setState(() => _times = t),
            onCommentChanged: (c) => _comment = c,
          ),
        ),
      ),
    );
  }
}
