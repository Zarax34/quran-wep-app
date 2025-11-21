package com.qurancenter.model;

import jakarta.persistence.*;
import lombok.Data;

@Data
@Entity
@Table(name = "alumni")
public class Alumni {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Integer id;

    @Column(nullable = false, length = 100)
    private String name;

    @Column(name = "graduation_year", nullable = false)
    private Integer graduationYear;

    @Column(columnDefinition = "TEXT")
    private String testimonial;

    @Column(length = 200)
    private String photo;
}
