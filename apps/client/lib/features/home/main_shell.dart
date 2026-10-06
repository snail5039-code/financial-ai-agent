// 로그인 뒤 하단 탭: 홈 / 대화 / 승인 대기 / 기록 / 설정

import 'package:flutter/material.dart';

import '../../common/common.dart';
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

  static const _menu = [
    (Icons.home_outlined, '홈'),
    (Icons.chat_bubble_outline, '대화'),
    (Icons.fact_check_outlined, '승인 대기'),
    (Icons.history, '기록'),
    (Icons.settings_outlined, '설정'),
  ];

  @override
  Widget build(BuildContext context) {
    final pages = IndexedStack(index: _tab, children: [
      readable(HomePage(onAsk: _ask, active: _tab == 0)),
      ChatPage(_conversation), // 대화는 넓은 화면에서 오른쪽 처리안 패널까지 쓰므로 폭을 줄이지 않는다
      readable(ApprovalsPage(active: _tab == 2)),
      readable(HistoryPage(active: _tab == 3)),
      readable(const SettingsPage()),
    ]);
    void select(int index) => setState(() => _tab = index);

    if (isWide(context)) {
      // 넓은 화면(웹): 왼쪽 메뉴 + 본문
      return Scaffold(
        body: Row(children: [
          NavigationRail(
            selectedIndex: _tab,
            onDestinationSelected: select,
            labelType: NavigationRailLabelType.all,
            destinations: [for (final (icon, label) in _menu) NavigationRailDestination(icon: Icon(icon), label: Text(label))],
          ),
          const VerticalDivider(width: 1),
          Expanded(child: pages),
        ]),
      );
    }
    return Scaffold(
      body: pages,
      bottomNavigationBar: NavigationBar(
        selectedIndex: _tab,
        onDestinationSelected: select,
        destinations: [for (final (icon, label) in _menu) NavigationDestination(icon: Icon(icon), label: label)],
      ),
    );
  }
}
