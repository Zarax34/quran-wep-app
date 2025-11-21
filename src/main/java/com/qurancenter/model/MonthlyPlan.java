package com.qurancenter.model;

import jakarta.persistence.*;
import lombok.Data;
import java.time.LocalDate;
import java.time.LocalDateTime;

@Data
@Entity
@Table(name = "monthly_plan")
public class MonthlyPlan {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Integer id;

    @Column(name = "student_id", nullable = false)
    private Integer studentId;

    @ManyToOne
    @JoinColumn(name = "student_id", insertable = false, updatable = false)
    private Student student;

    @Column(name = "start_date", nullable = false)
    private LocalDate startDate;

    @Column(name = "end_date", nullable = false)
    private LocalDate endDate;

    @Column(name = "plan_type", length = 20)
    private String planType = "حفظ";

    @Column(name = "start_surah", length = 100)
    private String startSurah;

    @Column(name = "start_verse")
    private Integer startVerse;

    @Column(name = "end_surah", length = 100)
    private String endSurah;

    @Column(name = "end_verse")
    private Integer endVerse;

    @Column(name = "daily_pages")
    private Float dailyPages;

    @Column(name = "total_pages")
    private Float totalPages;

    @Column(columnDefinition = "TEXT")
    private String notes;

    @Column(name = "created_at")
    private LocalDateTime createdAt = LocalDateTime.now();
}
