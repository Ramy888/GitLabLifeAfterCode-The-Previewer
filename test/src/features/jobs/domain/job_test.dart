import 'package:flutter_test/flutter_test.dart';
import 'package:starter_architecture_flutter_firebase/src/features/jobs/domain/job.dart';

void main() {
  group('fromMap', () {
    test('job with all properties', () {
      final job = Job.fromMap(const {
        'name': 'Blogging',
        'ratePerHour': 10,
      }, 'abc');
      expect(job, const Job(name: 'Blogging', ratePerHour: 10, id: 'abc'));
    });

    test('missing name', () {
      // * If the 'name' is missing, this error will be emitted:
      // * _CastError:<type 'Null' is not a subtype of type 'String' in type cast>
      // * We can detect it by expecting that the test throws a TypeError
      expect(
          () => Job.fromMap(const {
                'ratePerHour': 10,
              }, 'abc'),
          throwsA(isInstanceOf<TypeError>()));
    });
  });

  group('toMap', () {
    test('valid name, ratePerHour', () {
      const job = Job(name: 'Blogging', ratePerHour: 10, id: 'abc');
      expect(job.toMap(), {
        'name': 'Blogging',
        'ratePerHour': 10,
      });
    });
  });

  group('equality', () {
    test('different properties, equality returns false', () {
      const job1 = Job(name: 'Blogging', ratePerHour: 10, id: 'abc');
      const job2 = Job(name: 'Blogging', ratePerHour: 5, id: 'abc');
      expect(job1 == job2, false);
    });
    test('same properties, equality returns true', () {
      const job1 = Job(name: 'Blogging', ratePerHour: 10, id: 'abc');
      const job2 = Job(name: 'Blogging', ratePerHour: 10, id: 'abc');
      expect(job1 == job2, true);
    });
  });

  group('rate', () {
    test('fromMap reads an old whole-number rate and a decimal one', () {
      expect(Job.fromMap(const {'name': 'A', 'ratePerHour': 10}, 'x').ratePerHour, 10.0);
      expect(Job.fromMap(const {'name': 'A', 'ratePerHour': 12.5}, 'x').ratePerHour, 12.5);
    });
    test('parseRate accepts decimals and blanks, and rejects bad input instead of saving 0', () {
      expect(Job.parseRate('12.50'), 12.5);
      expect(Job.parseRate(' 8 '), 8.0);
      expect(Job.parseRate('12,50'), 12.5);
      expect(Job.parseRate(''), 0.0);
      expect(Job.parseRate('abc'), isNull);
      expect(Job.parseRate('-3'), isNull);
      expect(Job.parseRate('100000'), isNull);
      expect(Job.parseRate('1,000'), 1000.0);
      expect(Job.parseRate('1,234.50'), 1234.5);
      expect(Job.parseRate('1,2,3'), isNull);
    });
    test('a whole-number rate is stored as an integer, so older app versions can still read it', () {
      expect(const Job(id: 'a', name: 'A', ratePerHour: 12).toMap()['ratePerHour'], isA<int>());
      expect(const Job(id: 'a', name: 'A', ratePerHour: 12.5).toMap()['ratePerHour'], 12.5);
    });
  });
}
