# LIFE (Localized Intelligent Fleet Ecosystem)

## Overview

LIFE (Localized Intelligent Fleet Ecosystem) is a small-scale swarm robotics project focused on centralized vision-based robot coordination.

The system consists of multiple 3D-printed differential-drive robots operating inside a controlled arena. Instead of relying on onboard localization sensors, robot positions and orientations are estimated using an overhead camera and ArUco markers. A Raspberry Pi 5 acts as the central controller, continuously tracking the robots and issuing navigation commands over Wi-Fi.

LIFE is designed as a platform for exploring:

* Swarm Robotics
* Multi-Robot Coordination
* Computer Vision
* Autonomous Navigation
* Formation Control
* Human-Robot Interaction

---

## Vision

The long-term vision of LIFE is to create a scalable fleet of intelligent robots that can be monitored, coordinated, and controlled through a centralized perception system.

Rather than each robot carrying expensive sensors and computational hardware, intelligence is moved to a central controller that observes the environment, understands robot states, and coordinates collective behavior.

This approach enables experimentation with advanced robotics concepts while keeping individual robots simple, modular, and affordable.

---

## System Architecture

```text
                    Overhead Camera
                           |
                           v

                  Raspberry Pi 5
            (Vision + Localization +
                 Decision Making)
                           |
                      Wi-Fi UDP
                           |
        +------------------+------------------+
        |                                     |
        v                                     v

     Robot A                              Robot B
  (Uno R4 WiFi)                        (Uno R4 WiFi)
      L298N                                L298N
    BO Motors                           BO Motors
```

---

## Current Prototype

Each robot features:

* Fully 3D-Printed Chassis
* Arduino Uno R4 WiFi
* L298N Motor Driver
* BO Geared Motors
* Differential Drive Configuration
* 80 mm ArUco Marker Platform

Central infrastructure:

* Raspberry Pi 5
* Raspberry Pi Camera
* OpenCV ArUco Detection
* Wi-Fi Communication

---

## Current Capabilities

* Real-time robot localization
* Position and heading estimation
* Click-to-target navigation
* Simultaneous control of multiple robots
* Wireless command transmission
* Safety watchdog system

---

## Future Roadmap

* Encoder-based odometry
* Formation control
* Path planning algorithms
* Dynamic obstacle avoidance
* Multi-agent coordination
* Swarm behaviors
* Scalable fleet management

---

## Project Objective

Develop a robust research and educational platform for studying vision-based autonomous navigation and multi-robot systems using a centralized intelligence architecture.
