import 'dart:ui';
import 'package:flutter/material.dart';
import '../core/api_client.dart';
import '../core/theme.dart';

class ChatScreen extends StatefulWidget {
  final String comparisonId;

  const ChatScreen({super.key, required this.comparisonId});

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatMessage {
  final String text;
  final bool isUser;
  _ChatMessage({required this.text, required this.isUser});
}

class _ChatScreenState extends State<ChatScreen> {
  final ApiClient _apiClient = ApiClient();
  final TextEditingController _controller = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  final List<_ChatMessage> _messages = [];
  bool _isStreaming = false;

  final List<_QuickQuestion> _quickQuestions = [
    _QuickQuestion('⚖️ Законен ли коэффициент 3.0?', 'Законно ли начисление коэффициента 3.0 за ХВС по ПП РФ № 354?'),
    _QuickQuestion('📋 Какие нормы нарушил Водоканал?', 'Какие статьи закона нарушил Водоканал при применении коэффициента 3.0 без акта ИПУ?'),
    _QuickQuestion('📬 Куда жаловаться?', 'Куда жаловаться, если КГУП «Приморский водоканал» откажет в перерасчёте?'),
    _QuickQuestion('📄 Нужен ли акт ИПУ?', 'Обязан ли поставщик составить акт ИПУ перед применением коэффициента?'),
    _QuickQuestion('💰 Как взыскать переплату?', 'Как взыскать переплату 686.56 ₽ через суд или ГЖИ?'),
    _QuickQuestion('⏱️ Какой срок ответа на претензию?', 'В какой срок КГУП обязан ответить на досудебную претензию?'),
  ];

  @override
  void initState() {
    super.initState();
    _messages.add(_ChatMessage(
      text: 'Здравствуйте! Я ваш юридический консультант по ЖКХ и ПП РФ № 354. '
          'Я изучил результаты факторного анализа по вашей квитанции. '
          'Обнаружено незаконное начисление коэффициента 3.0 КГУП «Приморский водоканал» — '
          'переплата 686.56 ₽. Готов разъяснить законность начислений и порядок оспаривания. '
          'О чём хотите узнать?',
      isUser: false,
    ));
  }

  @override
  void dispose() {
    _controller.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  void _sendMessage(String text) async {
    final query = text.trim();
    if (query.isEmpty || _isStreaming) return;

    _controller.clear();
    setState(() {
      _messages.add(_ChatMessage(text: query, isUser: true));
      _messages.add(_ChatMessage(text: '', isUser: false));
      _isStreaming = true;
    });

    _scrollToBottom();

    try {
      final stream = _apiClient.streamChat(widget.comparisonId, query);
      await for (final token in stream) {
        if (!mounted) break;
        setState(() {
          final lastIdx = _messages.length - 1;
          _messages[lastIdx] = _ChatMessage(
            text: _messages[lastIdx].text + token,
            isUser: false,
          );
        });
        _scrollToBottom();
      }
    } finally {
      if (mounted) setState(() => _isStreaming = false);
    }
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 200),
          curve: Curves.easeOut,
        );
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Stack(
        children: [
          Container(decoration: const BoxDecoration(gradient: kDarkBgGradient)),

          // Ambient accent glow
          Positioned(
            top: -60,
            left: -40,
            child: Container(
              width: 220,
              height: 220,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                gradient: RadialGradient(
                  colors: [
                    AppColors.lavender.withOpacity(0.12),
                    Colors.transparent,
                  ],
                ),
              ),
            ),
          ),

          SafeArea(
            child: Column(
              children: [
                // AppBar
                _buildAppBar(context),
                const SizedBox(height: 8),

                // Messages list (SSE token stream)
                Expanded(
                  child: ListView.builder(
                    controller: _scrollController,
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                    itemCount: _messages.length,
                    itemBuilder: (context, index) {
                      final msg = _messages[index];
                      return _buildMessageBubble(msg, index == _messages.length - 1);
                    },
                  ),
                ),

                // Quick question chips
                if (!_isStreaming) _buildQuickChips(),
                const SizedBox(height: 6),

                // Input bar
                _buildInputBar(),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildAppBar(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 0),
      child: Row(
        children: [
          GestureDetector(
            onTap: () => Navigator.of(context).pop(),
            child: Container(
              padding: const EdgeInsets.all(8),
              decoration: GlassDecoration.dark(radius: 10),
              child: const Icon(Icons.arrow_back_ios_new_rounded,
                  size: 16, color: AppColors.textSecondary),
            ),
          ),
          const SizedBox(width: 10),
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: [
                  AppColors.lavender.withOpacity(0.20),
                  AppColors.violet.withOpacity(0.12),
                ],
              ),
              borderRadius: BorderRadius.circular(10),
              border: Border.all(color: AppColors.lavender.withOpacity(0.30)),
            ),
            child: const Icon(Icons.gavel_rounded, color: AppColors.lavender, size: 18),
          ),
          const SizedBox(width: 10),
          const Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                'AI-Юрист ЖКХ',
                style: TextStyle(
                  fontSize: 15,
                  fontWeight: FontWeight.w700,
                  color: AppColors.textPrimary,
                ),
              ),
              Text(
                'ПП РФ № 354 • ст. 157 ЖК РФ',
                style: TextStyle(fontSize: 10.5, color: AppColors.textMuted),
              ),
            ],
          ),
          const Spacer(),
          // Streaming indicator
          if (_isStreaming)
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              decoration: BoxDecoration(
                color: AppColors.successGreenBg,
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: AppColors.successGreen.withOpacity(0.35)),
              ),
              child: const Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  SizedBox(
                    width: 8,
                    height: 8,
                    child: CircularProgressIndicator(
                      strokeWidth: 1.5,
                      color: AppColors.successGreen,
                    ),
                  ),
                  SizedBox(width: 5),
                  Text(
                    'SSE',
                    style: TextStyle(
                      fontSize: 10,
                      color: AppColors.successGreen,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ],
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildMessageBubble(_ChatMessage msg, bool isLast) {
    final isEmpty = msg.text.isEmpty && !msg.isUser;

    return Align(
      alignment: msg.isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.only(bottom: 10),
        padding: const EdgeInsets.all(14),
        constraints: BoxConstraints(
          maxWidth: MediaQuery.of(context).size.width * 0.84,
        ),
        decoration: msg.isUser
            ? BoxDecoration(
                gradient: const LinearGradient(
                  colors: [AppColors.lavender, AppColors.violet],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: const BorderRadius.only(
                  topLeft: Radius.circular(18),
                  topRight: Radius.circular(18),
                  bottomLeft: Radius.circular(18),
                  bottomRight: Radius.circular(4),
                ),
              )
            : BoxDecoration(
                color: AppColors.glassFill,
                borderRadius: const BorderRadius.only(
                  topLeft: Radius.circular(4),
                  topRight: Radius.circular(18),
                  bottomLeft: Radius.circular(18),
                  bottomRight: Radius.circular(18),
                ),
                border: Border.all(color: AppColors.glassBorder),
              ),
        child: isEmpty
            ? Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  SizedBox(
                    width: 14,
                    height: 14,
                    child: CircularProgressIndicator(
                      strokeWidth: 1.5,
                      color: AppColors.lavender.withOpacity(0.7),
                    ),
                  ),
                  const SizedBox(width: 8),
                  const Text(
                    'Формирую ответ...',
                    style: TextStyle(
                      fontSize: 13,
                      color: AppColors.textMuted,
                      fontStyle: FontStyle.italic,
                    ),
                  ),
                ],
              )
            : Text(
                msg.text,
                style: TextStyle(
                  fontSize: 13.5,
                  height: 1.5,
                  color: msg.isUser ? AppColors.bgDeep : AppColors.textPrimary,
                  fontWeight: msg.isUser ? FontWeight.w500 : FontWeight.w400,
                ),
              ),
      ),
    );
  }

  Widget _buildQuickChips() {
    return SizedBox(
      height: 44,
      child: ListView.separated(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 16),
        itemCount: _quickQuestions.length,
        separatorBuilder: (_, __) => const SizedBox(width: 8),
        itemBuilder: (context, index) {
          final qq = _quickQuestions[index];
          return GestureDetector(
            onTap: () => _sendMessage(qq.query),
            child: Container(
              alignment: Alignment.center,
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
              decoration: BoxDecoration(
                color: AppColors.glassFill,
                borderRadius: BorderRadius.circular(20),
                border: Border.all(color: AppColors.glassBorder),
              ),
              child: Text(
                qq.label,
                style: const TextStyle(
                  fontSize: 12,
                  color: AppColors.textSecondary,
                  fontWeight: FontWeight.w500,
                ),
              ),
            ),
          );
        },
      ),
    );
  }

  Widget _buildInputBar() {
    return ClipRRect(
      child: BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 20, sigmaY: 20),
        child: Container(
          padding: const EdgeInsets.fromLTRB(16, 10, 16, 20),
          decoration: BoxDecoration(
            color: AppColors.bgDeep.withOpacity(0.80),
            border: Border(top: BorderSide(color: AppColors.glassBorder.withOpacity(0.5))),
          ),
          child: Row(
            children: [
              Expanded(
                child: Container(
                  decoration: GlassDecoration.dark(radius: 24),
                  child: TextField(
                    controller: _controller,
                    enabled: !_isStreaming,
                    textInputAction: TextInputAction.send,
                    onSubmitted: _sendMessage,
                    style: const TextStyle(
                      color: AppColors.textPrimary,
                      fontSize: 14,
                    ),
                    decoration: InputDecoration(
                      hintText: 'Задайте вопрос по начислению...',
                      hintStyle: const TextStyle(
                        color: AppColors.textMuted,
                        fontSize: 14,
                      ),
                      filled: false,
                      contentPadding: const EdgeInsets.symmetric(
                        horizontal: 18,
                        vertical: 12,
                      ),
                      border: InputBorder.none,
                      enabledBorder: InputBorder.none,
                      focusedBorder: InputBorder.none,
                    ),
                  ),
                ),
              ),
              const SizedBox(width: 8),
              GestureDetector(
                onTap: _isStreaming ? null : () => _sendMessage(_controller.text),
                child: Container(
                  width: 44,
                  height: 44,
                  decoration: BoxDecoration(
                    gradient: _isStreaming
                        ? null
                        : const LinearGradient(
                            colors: [AppColors.lavender, AppColors.violet],
                            begin: Alignment.topLeft,
                            end: Alignment.bottomRight,
                          ),
                    color: _isStreaming ? AppColors.glassFill : null,
                    borderRadius: BorderRadius.circular(22),
                    boxShadow: _isStreaming
                        ? null
                        : [
                            BoxShadow(
                              color: AppColors.violet.withOpacity(0.35),
                              blurRadius: 12,
                              offset: const Offset(0, 3),
                            ),
                          ],
                  ),
                  child: _isStreaming
                      ? const Padding(
                          padding: EdgeInsets.all(12),
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            color: AppColors.lavender,
                          ),
                        )
                      : const Icon(
                          Icons.send_rounded,
                          color: AppColors.bgDeep,
                          size: 20,
                        ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _QuickQuestion {
  final String label;
  final String query;
  const _QuickQuestion(this.label, this.query);
}
