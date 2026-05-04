import 'package:flutter/material.dart';

class AlertsScreen extends StatelessWidget {
  const AlertsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0F172A),
      appBar: AppBar(
        title: const Text("Alerts"),
      ),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: ListView(
          children: [
            _buildAlertCard(
              title: "High Fatigue Detected",
              message: "You have been active for 3+ hours continuously.",
              suggestion: "Take a 10–15 minute break.",
              color: Colors.red,
              icon: Icons.warning,
            ),
            _buildAlertCard(
              title: "Moderate Fatigue",
              message: "Your activity level is increasing steadily.",
              suggestion: "Consider short breaks between tasks.",
              color: Colors.orange,
              icon: Icons.error_outline,
            ),
            _buildAlertCard(
              title: "Low Risk",
              message: "Your usage pattern is balanced.",
              suggestion: "Keep maintaining healthy habits.",
              color: Colors.green,
              icon: Icons.check_circle,
            ),
            const SizedBox(height: 20),
            _buildInfoCard(),
          ],
        ),
      ),
    );
  }

  // 🚨 Alert Card
  Widget _buildAlertCard({
    required String title,
    required String message,
    required String suggestion,
    required Color color,
    required IconData icon,
  }) {
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF1E293B),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: color.withOpacity(0.6)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, color: color, size: 28),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: TextStyle(
                    color: color,
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 6),
                Text(
                  message,
                  style: const TextStyle(color: Colors.white70),
                ),
                const SizedBox(height: 6),
                Text(
                  suggestion,
                  style: const TextStyle(color: Colors.white54),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  // ℹ️ Info Card (AI Explanation)
  Widget _buildInfoCard() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF1E293B),
        borderRadius: BorderRadius.circular(20),
      ),
      child: const Text(
        "Alerts are generated based on AI-driven analysis of your usage patterns, including screen time, activity level, and interaction behavior.",
        style: TextStyle(color: Colors.white70),
      ),
    );
  }
}