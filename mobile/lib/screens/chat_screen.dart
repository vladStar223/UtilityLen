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

  final List<String> _quickQuestions = [
    "Законно ли начисление коэффициента 3.0?",
    "Какие статьи закона нарушил Водоканал?",
    "Куда жаловаться, если УК откажет?",
  ];

  @override
  void initState() {
    super.initState();
    // Приветственное сообщение от юридического ассистента
    _messages.add(
      _ChatMessage(
        text: "Здравствуйте! Я ваш юридический консультант по ЖКХ и ПП РФ № 354. "
            "Я изучил результаты факторного анализа по вашей квитанции. "
            "Готов разъяснить законность начислений и порядок оспаривания. О чем хотите узнать?",
        isUser: false,
      ),
    );
  }

  void _sendMessage(String text) async {
    final query = text.trim();
    if (query.isEmpty || _isStreaming) return;

    _controller.clear();
    setState(() {
      _messages.add(_ChatMessage(text: query, isUser: true));
      _messages.add(_ChatMessage(text: "", isUser: false));
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
      appBar: AppBar(
        title: const Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.gavel, color: AppTheme.accentCyan, size: 20),
            SizedBox(width: 8),
            Text("AI-Юрист ЖКХ"),
          ],
        ),
      ),
      body: Column(
        children: [
          // Сообщения чата
          Expanded(
            child: ListView.builder(
              controller: _scrollController,
              padding: const EdgeInsets.all(16),
              itemCount: _messages.length,
              itemBuilder: (context, index) {
                final msg = _messages[index];
                return _buildMessageBubble(msg);
              },
            ),
          ),

          // Быстрые подсказки вопросов
          if (!_isStreaming)
            SizedBox(
              height: 40,
              child: ListView.separated(
                scrollDirection: Axis.horizontal,
                padding: const EdgeInsets.symmetric(horizontal: 16),
                itemCount: _quickQuestions.length,
                separatorBuilder: (_, __) => const SizedBox(width: 8),
                itemBuilder: (context, index) {
                  return ActionChip(
                    label: Text(
                      _quickQuestions[index],
                      style: const TextStyle(fontSize: 12, color: Colors.white70),
                    ),
                    backgroundColor: AppTheme.darkCard,
                    side: BorderSide(color: Colors.white.withOpacity(0.12)),
                    onPressed: () => _sendMessage(_quickQuestions[index]),
                  );
                },
              ),
            ),
          const SizedBox(height: 8),

          // Поле ввода
          Container(
            padding: const EdgeInsets.fromLTRB(16, 8, 16, 16),
            decoration: BoxDecoration(
              color: AppTheme.darkCard,
              border: Border(top: BorderSide(color: Colors.white.withOpacity(0.08))),
            ),
            child: SafeArea(
              child: Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _controller,
                      enabled: !_isStreaming,
                      textInputAction: TextInputAction.send,
                      onSubmitted: _sendMessage,
                      decoration: InputDecoration(
                        hintText: "Задайте вопрос по начислению...",
                        hintStyle: TextStyle(color: Colors.white.withOpacity(0.4), fontSize: 14),
                        filled: true,
                        fillColor: AppTheme.darkBackground,
                        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(24),
                          borderSide: BorderSide.none,
                        ),
                      ),
                      style: const TextStyle(color: Colors.white, fontSize: 14),
                    ),
                  ),
                  const SizedBox(width: 8),
                  IconButton(
                    onPressed: _isStreaming ? null : () => _sendMessage(_controller.text),
                    icon: _isStreaming
                        ? const SizedBox(
                            width: 20,
                            height: 20,
                            child: CircularProgressIndicator(
                              strokeWidth: 2,
                              color: AppTheme.accentCyan,
                            ),
                          )
                        : const Icon(Icons.send_rounded, color: AppTheme.accentCyan),
                    style: IconButton.styleFrom(
                      backgroundColor: AppTheme.primaryBlue.withOpacity(0.2),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMessageBubble(_ChatMessage msg) {
    return Align(
      alignment: msg.isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.only(bottom: 12),
        padding: const EdgeInsets.all(14),
        constraints: BoxConstraints(
          maxWidth: MediaQuery.of(context).size.width * 0.82,
        ),
        decoration: BoxDecoration(
          color: msg.isUser ? AppTheme.primaryBlue : AppTheme.darkCard,
          borderRadius: BorderRadius.only(
            topLeft: const Radius.circular(16),
            topRight: const Radius.circular(16),
            bottomLeft: Radius.circular(msg.isUser ? 16 : 4),
            bottomRight: Radius.circular(msg.isUser ? 4 : 16),
          ),
          border: Border.all(
            color: msg.isUser ? Colors.transparent : Colors.white.withOpacity(0.08),
          ),
        ),
        child: Text(
          msg.text.isEmpty && !msg.isUser ? "Печатает ответ..." : msg.text,
          style: TextStyle(
            fontSize: 13.5,
            height: 1.45,
            color: msg.text.isEmpty ? Colors.white38 : Colors.white,
          ),
        ),
      ),
    );
  }
}
