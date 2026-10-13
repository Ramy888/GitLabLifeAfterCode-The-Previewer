import 'package:equatable/equatable.dart';
import 'package:flutter/foundation.dart';

typedef JobID = String;

@immutable
class Job extends Equatable {
  const Job({required this.id, required this.name, required this.ratePerHour});
  final JobID id;
  final String name;
  /// Pay per hour in the user's currency; 0 means unpaid. Stored as a Firestore number (older jobs hold whole numbers).
  final double ratePerHour;

  /// Highest rate the form accepts, to catch a mistyped extra zero.
  static const maxRate = 9999.0;

  /// Parses the rate field: blank is 0; "12,50" uses a decimal comma; "1,000" and "1,234.50" use thousands commas.
  /// Anything that isn't a number from 0 to [maxRate] returns null, so the form shows an error instead of saving 0.
  static double? parseRate(String input) {
    var text = input.trim();
    if (RegExp(r'^\d+,\d{1,2}$').hasMatch(text)) {
      text = text.replaceAll(',', '.');
    } else if (RegExp(r'^\d{1,3}(,\d{3})+(\.\d+)?$').hasMatch(text)) {
      text = text.replaceAll(',', '');
    }
    if (text.isEmpty) return 0.0;
    final rate = double.tryParse(text);
    if (rate == null || rate.isNaN || rate < 0 || rate > maxRate) return null;
    return rate;
  }

  @override
  List<Object> get props => [name, ratePerHour];

  @override
  bool get stringify => true;

  factory Job.fromMap(Map<String, dynamic> data, String id) {
    final name = data['name'] as String;
    final ratePerHour = (data['ratePerHour'] as num).toDouble();
    return Job(
      id: id,
      name: name,
      ratePerHour: ratePerHour,
    );
  }

  Map<String, dynamic> toMap() {
    return {
      'name': name,
      // Whole rates stay integers in Firestore, so app versions before 2.2.0 (which read an int) keep working.
      'ratePerHour': ratePerHour == ratePerHour.roundToDouble() ? ratePerHour.toInt() : ratePerHour,
    };
  }
}
