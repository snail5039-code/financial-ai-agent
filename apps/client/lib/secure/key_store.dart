// 증권사 키·계좌번호 저장 (FR-05, NFR-02). 폰 보안 저장소(Android Keystore)에만 두고 서버로 보내지 않는다.
// 웹 빌드에는 키 입력 화면이 없으므로 여기 값도 쓰지 않는다.

import 'package:flutter_secure_storage/flutter_secure_storage.dart';

/// 보안 저장소. 테스트에서는 memory()로 기기 없이 쓴다
class SecureBox {
  SecureBox() : _memory = null;
  SecureBox.memory() : _memory = {};

  static const _storage = FlutterSecureStorage();
  final Map<String, String>? _memory;

  Future<String?> read(String key) async => _memory != null ? _memory[key] : await _storage.read(key: key);

  Future<void> write(String key, String value) async {
    if (_memory != null) {
      _memory[key] = value;
    } else {
      await _storage.write(key: key, value: value);
    }
  }

  Future<void> delete(String key) async {
    if (_memory != null) {
      _memory.remove(key);
    } else {
      await _storage.delete(key: key);
    }
  }
}

final secureBox = SecureBox();

/// KIS 계좌번호는 "앞 8자리-뒤 2자리"(종합계좌번호-상품코드)
final accountPattern = RegExp(r'^(\d{8})-?(\d{2})$');

class BrokerKeys {
  BrokerKeys({required this.appKey, required this.appSecret, required this.account}) {
    if (!accountPattern.hasMatch(account)) throw const FormatException('계좌번호는 12345678-01 형식이에요');
  }

  final String appKey;
  final String appSecret;
  final String account;

  String get cano => accountPattern.firstMatch(account)!.group(1)!;
  String get productCode => accountPattern.firstMatch(account)!.group(2)!;

  static Future<BrokerKeys?> load(SecureBox box) async {
    final appKey = await box.read('kis_app_key');
    final appSecret = await box.read('kis_app_secret');
    final account = await box.read('kis_account');
    if (appKey == null || appSecret == null || account == null) return null;
    return BrokerKeys(appKey: appKey, appSecret: appSecret, account: account);
  }

  Future<void> save(SecureBox box) async {
    await box.write('kis_app_key', appKey);
    await box.write('kis_app_secret', appSecret);
    await box.write('kis_account', account);
  }

  static Future<void> delete(SecureBox box) async {
    for (final key in ['kis_app_key', 'kis_app_secret', 'kis_account', 'kis_token', 'kis_token_expires']) {
      await box.delete(key);
    }
  }
}
