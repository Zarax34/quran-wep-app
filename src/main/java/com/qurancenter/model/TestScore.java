package com.qurancenter.model;

import jakarta.persistence.*;
import lombok.Data;
import java.time.LocalDateTime;

@Data
@Entity
@Table(name = "test_score")
public class TestScore {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Integer id;

    @Column(name = "student_id", nullable = false)
    private Integer studentId;

    @ManyToOne
    @JoinColumn(name = "student_id", insertable = false, updatable = false)
    private Student student;

    @Column(name = "test_id", nullable = false)
    private Integer testId;

    @ManyToOne
    @JoinColumn(name = "test_id", insertable = false, updatable = false)
    private Test test;

    @Column(nullable = false)
    private Float score;

    @Column(name = "recorded_by_id", nullable = false)
    private Integer recordedById;

    @ManyToOne
    @JoinColumn(name = "recorded_by_id", insertable = false, updatable = false)
    private User recorder;

    @Column(name = "recorded_at")
    private LocalDateTime recordedAt = LocalDateTime.now();
}
