import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:google_fonts/google_fonts.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/theme/rx_theme_ext.dart';
import '../../../core/widgets/shared_widgets.dart';
import '../../../data/models/notification_model.dart';
import '../bloc/home_bloc.dart';

class NotificationsScreen extends StatefulWidget {
  const NotificationsScreen({super.key});

  @override
  State<NotificationsScreen> createState() => _NotificationsScreenState();
}

class _NotificationsScreenState extends State<NotificationsScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) {
        context.read<HomeBloc>().add(LoadHomeDataEvent());
      }
    });
  }

  Color _c(NotificationType t) {
    switch (t) {
      case NotificationType.refill:
        return C.warn;
      case NotificationType.order:
        return C.ok;
      case NotificationType.safety:
        return C.err;
      case NotificationType.system:
        return C.compute;
    }
  }

  @override
  Widget build(BuildContext context) {
    final r = context.rx;
    return BlocBuilder<HomeBloc, HomeState>(
      builder: (context, state) {
        final notifs = state.notifications;
        return Scaffold(
          backgroundColor: r.bg,
          appBar: AppBar(
            backgroundColor: r.bg,
            leading: IconButton(icon: Icon(Icons.arrow_back_rounded, color: r.text1), onPressed: () => Navigator.pop(context)),
            title: Text('NOTIFICATIONS', style: GoogleFonts.outfit(color: r.text1, fontSize: 13, fontWeight: FontWeight.w700, letterSpacing: 2)),
          ),
          body: RefreshIndicator(
            onRefresh: () async {
              context.read<HomeBloc>().add(LoadHomeDataEvent());
              await Future<void>.delayed(const Duration(milliseconds: 350));
            },
            child: notifs.isEmpty
              ? ListView(children: const [SizedBox(height: 220), EmptyState(icon: Icons.notifications_off_outlined, title: 'No notifications')])
              : ListView.builder(
                  padding: const EdgeInsets.fromLTRB(24, 8, 24, 24),
                  itemCount: notifs.length,
                  itemBuilder: (_, i) {
                    final n = notifs[i];
                    final c = _c(n.type);
                    return Container(
                      margin: const EdgeInsets.only(bottom: 10),
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: r.card,
                        borderRadius: BorderRadius.circular(12),
                        border: !n.isRead ? Border(left: BorderSide(color: c, width: 3)) : Border.all(color: r.border.withOpacity(0.4)),
                      ),
                      child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
                        Padding(padding: const EdgeInsets.only(top: 4), child: Container(width: 7, height: 7, decoration: BoxDecoration(color: c, shape: BoxShape.circle))),
                        const SizedBox(width: 14),
                        Expanded(
                          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                            Text(n.title.toUpperCase(), style: GoogleFonts.outfit(color: r.text1, fontSize: 12, fontWeight: FontWeight.w700, letterSpacing: 0.5)),
                            const SizedBox(height: 4),
                            Text(n.body, style: GoogleFonts.outfit(color: r.text2, fontSize: 13, height: 1.45)),
                            const SizedBox(height: 6),
                            Text(_ago(n.createdAt).toUpperCase(), style: GoogleFonts.outfit(color: r.text3, fontSize: 9, fontWeight: FontWeight.w600, letterSpacing: 1)),
                          ]),
                        ),
                        if (n.hasAction) Icon(Icons.chevron_right_rounded, color: r.text3, size: 18),
                      ]),
                    );
                  },
                ),
          ),
        );
      },
    );
  }

  String _ago(DateTime d) {
    final df = DateTime.now().difference(d);
    return df.inMinutes < 60
        ? '${df.inMinutes}m ago'
        : df.inHours < 24
            ? '${df.inHours}h ago'
            : '${df.inDays}d ago';
  }
}
