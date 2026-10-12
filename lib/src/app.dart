import 'dart:developer';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:force_update_helper/force_update_helper.dart';
import 'package:starter_architecture_flutter_firebase/src/routing/app_router.dart';
import 'package:starter_architecture_flutter_firebase/src/routing/app_startup.dart';
import 'package:starter_architecture_flutter_firebase/src/routing/go_router_delegate_listener.dart';
import 'package:starter_architecture_flutter_firebase/src/utils/alert_dialogs.dart';
import 'package:url_launcher/url_launcher.dart';

class MyApp extends ConsumerWidget {
  const MyApp({super.key});

  /// This app's App Store Connect Apple ID, passed at build time with `--dart-define=IOS_APP_STORE_ID=<id>`.
  static const iosAppStoreId = String.fromEnvironment('IOS_APP_STORE_ID');

  static const primaryColor = Colors.indigo;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final goRouter = ref.watch(goRouterProvider);
    return MaterialApp.router(
      routerConfig: goRouter,
      builder: (_, child) {
        // * Important: Use AppStartupWidget to wrap ForceUpdateWidget otherwise you will get this error:
        // * Navigator operation requested with a context that does not include a Navigator.
        // * The context used to push or pop routes from the Navigator must be that of a widget that is a descendant of a Navigator widget.
        final routed = GoRouterDelegateListener(child: child!);
        return AppStartupWidget(
          // The force-update gate needs this app's own App Store ID; without one it stays off.
          onLoaded: (_) => iosAppStoreId.isEmpty
              ? routed
              : ForceUpdateWidget(
                  navigatorKey: goRouter.routerDelegate.navigatorKey,
                  forceUpdateClient: ForceUpdateClient(
                    // * Real apps should fetch this from an API endpoint or via
                    // * Firebase Remote Config
                    fetchRequiredVersion: () => Future.value('2.0.0'),
                    iosAppStoreId: iosAppStoreId,
                  ),
                  allowCancel: false,
                  showForceUpdateAlert: (context, allowCancel) =>
                      showAlertDialog(
                    context: context,
                    title: 'App Update Required',
                    content: 'Please update to continue using the app.',
                    cancelActionText: allowCancel ? 'Later' : null,
                    defaultActionText: 'Update Now',
                  ),
                  showStoreListing: (storeUrl) async {
                    if (await canLaunchUrl(storeUrl)) {
                      await launchUrl(
                        storeUrl,
                        // * Open app store app directly (or fallback to browser)
                        mode: LaunchMode.externalApplication,
                      );
                    } else {
                      log('Cannot launch URL: $storeUrl');
                    }
                  },
                  onException: (e, st) {
                    log(e.toString());
                  },
                  child: routed,
                ),
        );
      },
      theme: ThemeData(
        colorSchemeSeed: primaryColor,
        unselectedWidgetColor: Colors.grey,
        appBarTheme: const AppBarTheme(
          backgroundColor: primaryColor,
          foregroundColor: Colors.white,
          elevation: 2.0,
          centerTitle: true,
        ),
        scaffoldBackgroundColor: Colors.grey[200],
        dividerColor: Colors.grey[400],
        elevatedButtonTheme: ElevatedButtonThemeData(
          style: ElevatedButton.styleFrom(
            backgroundColor: primaryColor,
            foregroundColor: Colors.white,
          ),
        ),
        outlinedButtonTheme: OutlinedButtonThemeData(
          style: OutlinedButton.styleFrom(
            backgroundColor: primaryColor,
            foregroundColor: Colors.white,
          ),
        ),
        floatingActionButtonTheme: const FloatingActionButtonThemeData(
          backgroundColor: primaryColor,
        ),
      ),
      debugShowCheckedModeBanner: false,
    );
  }
}
