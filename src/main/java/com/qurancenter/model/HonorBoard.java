package com.qurancenter.model;

import jakarta.persistence.*;
import lombok.Data;

@Data
@Entity
@Table(name = "honor_board")
public class HonorBoard {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Integer id;

    @Column(name = "student_id", nullable = false)
    private Integer studentId;

    @ManyToOne
    @JoinColumn(name = "student_id", insertable = false, updatable = false)
    private Student student;

    @Column(nullable = false)
    private Integer month;

    @Column(nullable = false)
    private Integer year;

    private Integer rank;
}
