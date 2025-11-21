package com.qurancenter.model;

import jakarta.persistence.*;
import lombok.Data;
import lombok.ToString;
import java.time.LocalDateTime;
import java.util.List;

@Data
@Entity
@Table(name = "test")
public class Test {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Integer id;

    @Column(nullable = false, length = 150)
    private String name;

    @Column(name = "course_id", nullable = false)
    private Integer courseId;

    @ManyToOne
    @JoinColumn(name = "course_id", insertable = false, updatable = false)
    private Course course;

    @Column(name = "test_date", nullable = false)
    private LocalDateTime testDate = LocalDateTime.now();

    @Column(name = "max_score", nullable = false)
    private Float maxScore;

    @Column(name = "min_passing_score")
    private Float minPassingScore;

    @OneToMany(mappedBy = "test", cascade = CascadeType.ALL, orphanRemoval = true)
    @ToString.Exclude
    private List<TestScore> scores;
}
