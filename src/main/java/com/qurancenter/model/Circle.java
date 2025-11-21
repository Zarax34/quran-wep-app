package com.qurancenter.model;

import jakarta.persistence.*;
import lombok.Data;
import lombok.ToString;
import java.util.List;

@Data
@Entity
@Table(name = "circle")
public class Circle {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Integer id;

    @Column(nullable = false, length = 100)
    private String name;

    @Column(name = "teacher_id")
    private Integer teacherId;

    @ManyToOne
    @JoinColumn(name = "teacher_id", insertable = false, updatable = false)
    private User teacher;

    @Column(name = "teacher_name", length = 100)
    private String teacherName;

    @Column(name = "is_active")
    private Boolean isActive = true;

    @Column(name = "academic_year", length = 10)
    private String academicYear = "2025";

    @Column(length = 50)
    private String category; // شباب or أشبال

    @Column(name = "requires_approval")
    private Boolean requiresApproval = true;

    @OneToMany(mappedBy = "circle")
    @ToString.Exclude
    private List<Student> students;
}
