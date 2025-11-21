package com.qurancenter.model;

import jakarta.persistence.*;
import lombok.Data;
import java.time.LocalDate;

@Data
@Entity
@Table(name = "fee")
public class Fee {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Integer id;

    @Column(name = "student_id", nullable = false)
    private Integer studentId;

    @ManyToOne
    @JoinColumn(name = "student_id", insertable = false, updatable = false)
    private Student student;

    @Column(nullable = false)
    private Float amount;

    @Column(name = "date_paid")
    private LocalDate datePaid;

    @Column(length = 20)
    private String status = "Paid";

    @Column(length = 100)
    private String title;

    @Column(columnDefinition = "TEXT")
    private String notes;
}
