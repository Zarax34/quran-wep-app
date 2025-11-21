package com.qurancenter.model;

import jakarta.persistence.*;
import lombok.Data;
import java.time.LocalDate;

@Data
@Entity
@Table(name = "attendance")
public class Attendance {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Integer id;

    @Column(name = "student_id", nullable = false)
    private Integer studentId;

    @ManyToOne
    @JoinColumn(name = "student_id", insertable = false, updatable = false)
    private Student student;

    @Column(nullable = false)
    private LocalDate date;

    @Column(length = 20)
    private String status = "حاضر";

    @Column(columnDefinition = "TEXT")
    private String notes;

    @Column(name = "academic_year", length = 10)
    private String academicYear = "2025";
}
