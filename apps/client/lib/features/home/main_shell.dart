// 로그인 뒤 하단 탭: 홈 / 대화 / 승인 대기 / 기록 / 설정

import 'package:flutter/material.dart';

import '../approvals/approvals_page.dart';
import '../chat/chat_page.dart';
import '../chat/conversation.dart';
import '../history/history_page.dart';
import '../settings/settings_page.dart';
import 'home_page.dart';

class MainShell extends StatefulWidget {
  const MainShell({super.key});

  @override
  State<MainShell> createState() => _MainShellState();
}

class _MainShellState extends State<MainShell> {
  int _tab = 0;
  final _conversation = Conversation(); // 탭을 바꿔도 대화가 남게 여기서 가진다

  /// 홈의 추천 질문·입력창 → 대화 탭으로 가서 보낸다
  void _ask(String text) {
    setState(() => _tab = 1);
    _conversation.send(text);
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        body: IndexedStack(index: _tab, children: [
          HomePage(onAsk: _ask, active: _tab == 0),
          ChatPage(_conversation),
          ApprovalsPage(active: _tab == 2),
          HistoryPage(active: _tab == 3),
          const SettingsPage(),
        ]),
        bottomNavigationBar: NavigationBar(
          selectedIndex: _tab,
          onDestinationSelected: (index) => setState(() => _tab = index),
          destinations: const [
            NavigationDestination(icon: Icon(Icons.home_outlined), label: '홈'),
            NavigationDestination(icon: Icon(Icons.chat_bubble_outline), label: '대화'),
            NavigationDestination(icon: Icon(Icons.fact_check_outlined), label: '승인 대기'),
            NavigationDestination(icon: Icon(Icons.history), label: '기록'),
            NavigationDestination(icon: Icon(Icons.settings_outlined), label: '설정'),
          ],
        ),
      );
}
