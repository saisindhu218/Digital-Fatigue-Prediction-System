import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';

class DashboardScreen extends StatelessWidget {
  const DashboardScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0F172A),
      appBar: AppBar(
        title: const Text("Dashboard"),
      ),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: SingleChildScrollView(
          child: Column(
            children: [
              _buildScoreCards(),
              const SizedBox(height: 20),
              _buildScreenTimeCard(),
              const SizedBox(height: 20),
              _buildGraphCard(),
            ],
          ),
        ),
      ),
    );
  }

  // 🔴 Fatigue + 🟡 Productivity
  Widget _buildScoreCards() {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: const [
        _ScoreCard(
          title: "Fatigue",
          value: "72%",
          color: Colors.red,
        ),
        _ScoreCard(
          title: "Productivity",
          value: "58%",
          color: Colors.orange,
        ),
      ],
    );
  }

  // ⏱ Screen Time Card
  Widget _buildScreenTimeCard() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: const Color(0xFF1E293B),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Column(
        children: const [
          Text(
            "Total Screen Time",
            style: TextStyle(color: Colors.white70),
          ),
          SizedBox(height: 10),
          Text(
            "5h 32m",
            style: TextStyle(
              fontSize: 32,
              fontWeight: FontWeight.bold,
              color: Colors.white,
            ),
          ),
          SizedBox(height: 5),
          Text(
            "Laptop + Mobile",
            style: TextStyle(color: Colors.white54),
          ),
        ],
      ),
    );
  }

  // 📊 Graph Card with Labels + Colors
  Widget _buildGraphCard() {
    final usageData = [2.0, 3.0, 2.5, 4.0, 3.5, 5.0, 4.2];

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF1E293B),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            "Weekly Usage",
            style: TextStyle(color: Colors.white, fontSize: 16),
          ),
          const SizedBox(height: 20),
          SizedBox(
            height: 220,
            child: BarChart(
              BarChartData(
                gridData: FlGridData(show: false),
                borderData: FlBorderData(show: false),

                titlesData: FlTitlesData(
                  leftTitles: AxisTitles(
                    sideTitles: SideTitles(showTitles: false),
                  ),
                  rightTitles: AxisTitles(
                    sideTitles: SideTitles(showTitles: false),
                  ),
                  topTitles: AxisTitles(
                    sideTitles: SideTitles(showTitles: false),
                  ),
                  bottomTitles: AxisTitles(
                    sideTitles: SideTitles(
                      showTitles: true,
                      getTitlesWidget: (value, meta) {
                        const days = [
                          "Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"
                        ];
                        return Padding(
                          padding: const EdgeInsets.only(top: 8),
                          child: Text(
                            days[value.toInt()],
                            style: const TextStyle(
                              color: Colors.white70,
                              fontSize: 12,
                            ),
                          ),
                        );
                      },
                    ),
                  ),
                ),

                barGroups: List.generate(
                  usageData.length,
                  (index) => _buildBar(index, usageData[index]),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  // 🎯 Smart Color Bar Logic
  BarChartGroupData _buildBar(int x, double y) {
    Color barColor;

    if (y >= 4.5) {
      barColor = Colors.red; // 🔴 High
    } else if (y >= 3) {
      barColor = Colors.orange; // 🟡 Medium
    } else {
      barColor = Colors.green; // 🟢 Low
    }

    return BarChartGroupData(
      x: x,
      barRods: [
        BarChartRodData(
          toY: y,
          width: 14,
          color: barColor,
          borderRadius: BorderRadius.circular(6),
        ),
      ],
    );
  }
}

// 🔷 Reusable Score Card
class _ScoreCard extends StatelessWidget {
  final String title;
  final String value;
  final Color color;

  const _ScoreCard({
    required this.title,
    required this.value,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 160,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF1E293B),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Column(
        children: [
          Text(title, style: const TextStyle(color: Colors.white70)),
          const SizedBox(height: 10),
          Text(
            value,
            style: TextStyle(
              fontSize: 26,
              fontWeight: FontWeight.bold,
              color: color,
            ),
          ),
        ],
      ),
    );
  }
}