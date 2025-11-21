package com.qurancenter.model;

import jakarta.persistence.*;
import lombok.Data;
import java.time.LocalDate;

@Data
@Entity
@Table(name = "report")
public class Report {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Integer id;

    @Column(name = "student_id", nullable = false)
    private Integer studentId;

    @ManyToOne
    @JoinColumn(name = "student_id", insertable = false, updatable = false)
    private Student student;

    @Column(name = "teacher_id", nullable = false)
    private Integer teacherId;

    @ManyToOne
    @JoinColumn(name = "teacher_id", insertable = false, updatable = false)
    private User teacher;

    @Column(name = "circle_id", nullable = false)
    private Integer circleId;

    @ManyToOne
    @JoinColumn(name = "circle_id", insertable = false, updatable = false)
    private Circle circle;

    @Column(nullable = false)
    private LocalDate date;

    @Column(nullable = false, length = 100)
    private String surah;

    @Column(name = "from_verse", nullable = false)
    private Integer fromVerse;

    @Column(name = "to_verse", nullable = false)
    private Integer toVerse;

    @Column(nullable = false, length = 10)
    private String grade;

    @Column(length = 10)
    private String type = "حفظ";

    @Column(columnDefinition = "TEXT")
    private String notes;

    @Column(name = "academic_year", length = 10)
    private String academicYear = "2025";

    @Column(length = 20)
    private String status = "Approved";
}
