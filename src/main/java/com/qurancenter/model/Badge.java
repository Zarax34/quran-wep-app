package com.qurancenter.model;

import jakarta.persistence.*;
import lombok.Data;
import lombok.ToString;
import java.util.List;

@Data
@Entity
@Table(name = "badge")
public class Badge {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Integer id;

    @Column(nullable = false, length = 100)
    private String name;

    @Column(length = 200)
    private String description;

    @Column(length = 100)
    private String icon;

    @OneToMany(mappedBy = "badge")
    @ToString.Exclude
    private List<StudentBadge> studentBadges;
}
