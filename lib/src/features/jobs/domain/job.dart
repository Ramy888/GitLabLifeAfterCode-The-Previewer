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

  /// Parses the rate field: blank is 0, a comma works as the decimal point, and anything that isn't a number from 0 to
  /// [maxRate] returns null so the form can show an error instead of quietly saving 0.
  static double? parseRate(String input) {
    final text = input.trim().replaceAll(',', '.');
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
      'ratePerHour': ratePerHour,
    };
  }
}
