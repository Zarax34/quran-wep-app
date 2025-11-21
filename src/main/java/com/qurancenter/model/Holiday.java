package com.qurancenter.model;

import jakarta.persistence.*;
import lombok.Data;
import lombok.ToString;
import java.time.LocalDate;
import java.util.List;

@Data
@Entity
@Table(name = "holiday")
public class Holiday {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Integer id;

    @Column(nullable = false, unique = true)
    private LocalDate date;

    @Column(length = 200)
    private String reason;

    @Column(name = "has_attendance")
    private Boolean hasAttendance = false;

    @Column(name = "is_recurring")
    private Boolean isRecurring = false;

    @Column(name = "teacher_id")
    private Integer teacherId;

    @ManyToOne
    @JoinColumn(name = "teacher_id", insertable = false, updatable = false)
    private User teacher;

    @Column(name = "academic_year", length = 10)
    private String academicYear = "2025";

    @Column(length = 20)
    private String status = "Approved";

    @ManyToMany
    @JoinTable(
        name = "holiday_circles",
        joinColumns = @JoinColumn(name = "holiday_id"),
        inverseJoinColumns = @JoinColumn(name = "circle_id")
    )
    @ToString.Exclude
    private List<Circle> targetCircles;
}
