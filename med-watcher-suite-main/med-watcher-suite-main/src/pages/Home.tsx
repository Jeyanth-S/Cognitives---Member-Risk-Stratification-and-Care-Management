import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import heroImage from "@/assets/medical-hero.jpg";
import particlesBg from "@/assets/particles-bg.jpg";
import { useNavigate } from "react-router-dom";
import { 
  Activity, 
  Users, 
  TrendingUp, 
  TrendingDown,
  Minus,
  Shield, 
  Brain, 
  Heart,
  Phone,
  Mail,
  MapPin,
  CheckCircle,
  BarChart3,
  FileText,
  Stethoscope,
  Zap,
  Eye,
  Target,
  Star,
  Award
} from "lucide-react";


const Home = () => {
  // Sample data for visualizations
  const navigate = useNavigate();
  const diseaseStats = [
    { name: "COVID-19", affected: 2847, deaths: 89, trend: "down", trendIcon: TrendingDown, change: -12 },
    { name: "Diabetes", affected: 5632, deaths: 234, trend: "stable", trendIcon: Minus, change: 0 },
    { name: "Heart Disease", affected: 4521, deaths: 445, trend: "up", trendIcon: TrendingUp, change: +8 },
    { name: "Cancer", affected: 3289, deaths: 678, trend: "down", trendIcon: TrendingDown, change: -5 },
  ];

  const features = [
    {
      icon: Brain,
      title: "AI-Powered Predictions",
      description: "Advanced machine learning algorithms for accurate health predictions",
      gradient: "bg-gradient-primary"
    },
    {
      icon: Shield,
      title: "Data Security",
      description: "HIPAA-compliant platform ensuring complete patient data protection",
      gradient: "bg-gradient-success"
    },
    {
      icon: BarChart3,
      title: "Real-time Analytics",
      description: "Live monitoring and instant insights for critical decision making",
      gradient: "bg-gradient-warning"
    },
    {
      icon: Heart,
      title: "Patient-Centric",
      description: "Designed with patient care and outcomes as the primary focus",
      gradient: "bg-gradient-destructive"
    }
  ];

  return (
    <div className="min-h-screen bg-background relative overflow-hidden">
      {/* Animated Background Particles */}
      <div className="fixed inset-0 pointer-events-none">
        <div 
          className="absolute inset-0 opacity-5"
          style={{ backgroundImage: `url(${particlesBg})` }}
        />
        <div className="absolute top-20 left-10 w-72 h-72 bg-gradient-glow rounded-full animate-float" />
        <div className="absolute bottom-20 right-10 w-96 h-96 bg-gradient-glow rounded-full animate-float" style={{ animationDelay: '2s' }} />
      </div>

      {/* Header */}
      <header className="relative bg-gradient-primary shadow-intense">
        <div className="container mx-auto px-4 py-6 flex justify-between items-center">
          <div className="flex items-center space-x-3 animate-slide-up">
            <div className="p-2 bg-white/20 rounded-full backdrop-blur-sm animate-pulse-slow">
              <Activity className="w-8 h-8 text-primary-foreground" />
            </div>
            <h1 className="text-3xl font-bold text-primary-foreground">MedAnalytics</h1>
          </div>
          <nav className="hidden md:flex space-x-8">
            <a href="#dashboard" className="text-primary-foreground hover:text-primary-glow transition-smooth hover:scale-110 font-medium">Dashboard</a>
            <a href="#patients" className="text-primary-foreground hover:text-primary-glow transition-smooth hover:scale-110 font-medium">Patients</a>
            <a href="#analytics" className="text-primary-foreground hover:text-primary-glow transition-smooth hover:scale-110 font-medium">Analytics</a>
            <a href="#contact" className="text-primary-foreground hover:text-primary-glow transition-smooth hover:scale-110 font-medium">Contact</a>
          </nav>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative bg-gradient-hero text-primary-foreground py-24 overflow-hidden">
        <div 
          className="absolute inset-0 bg-cover bg-center opacity-30"
          style={{ backgroundImage: `url(${heroImage})` }}
        />
        <div className="absolute inset-0 bg-gradient-to-r from-primary/50 to-accent/50" />
        
        {/* Floating Elements */}
        <div className="absolute top-20 left-20 animate-float">
          <Stethoscope className="w-16 h-16 text-white/20" />
        </div>
        <div className="absolute bottom-20 right-20 animate-float" style={{ animationDelay: '1s' }}>
          <Heart className="w-20 h-20 text-white/20" />
        </div>
        
        <div className="relative container mx-auto px-4 text-center">
          <h2 className="text-6xl font-bold mb-8 animate-fade-in-up">
            Advanced Healthcare
            <span className="block text-accent-foreground">Analytics Platform</span>
          </h2>
          <p className="text-2xl mb-12 max-w-3xl mx-auto opacity-90 animate-fade-in-up" style={{ animationDelay: '0.2s' }}>
            Empowering healthcare professionals with AI-driven insights, real-time monitoring, 
            and predictive analytics for superior patient outcomes.
          </p>
          <div className="flex justify-center space-x-6 animate-fade-in-up" style={{ animationDelay: '0.4s' }}>
            <Button variant="secondary" size="lg" className="shadow-intense hover-glow group text-lg px-8 py-4" onClick={() => navigate("/patients")}>
              <FileText className="w-6 h-6 mr-3 group-hover:scale-110 transition-transform" />
              View Patient Details
            </Button>
            <Button variant="success" size="lg" className="shadow-intense hover-glow group text-lg px-8 py-4">
              <Brain className="w-6 h-6 mr-3 group-hover:scale-110 transition-transform" />
              Run AI Prediction
            </Button>
          </div>
        </div>
      </section>

      {/* Disease Statistics Dashboard */}
      <section id="dashboard" className="relative py-20 bg-muted/30">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16 animate-fade-in-up">
            <div className="inline-flex items-center justify-center p-3 bg-gradient-primary rounded-full mb-6 shadow-glow">
              <BarChart3 className="w-8 h-8 text-primary-foreground" />
            </div>
            <h3 className="text-4xl font-bold mb-6 gradient-text">Disease Statistics Overview</h3>
            <p className="text-muted-foreground max-w-3xl mx-auto text-lg">
              Real-time monitoring of patient infection rates and mortality statistics across severe diseases
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 mb-16">
            {diseaseStats.map((disease, index) => (
              <Card key={index} className="card-hover bg-gradient-card border-0 overflow-hidden animate-fade-in-up" style={{ animationDelay: `${index * 0.1}s` }}>
                <CardHeader className="pb-3 relative">
                  <div className="absolute top-0 right-0 w-20 h-20 bg-gradient-glow rounded-full -translate-y-10 translate-x-10" />
                  <CardTitle className="text-xl flex items-center justify-between relative z-10">
                    <span className="font-bold">{disease.name}</span>
                    <Badge 
                      variant={disease.trend === "up" ? "destructive" : disease.trend === "down" ? "default" : "secondary"}
                      className="shadow-elegant group"
                    >
                      <disease.trendIcon className="w-3 h-3 mr-1 group-hover:scale-110 transition-transform" />
                      {disease.change > 0 ? `+${disease.change}%` : disease.change === 0 ? '0%' : `${disease.change}%`}
                    </Badge>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex justify-between items-center p-3 bg-warning/10 rounded-lg">
                      <span className="text-muted-foreground font-medium">Affected:</span>
                      <span className="font-bold text-warning text-lg">{disease.affected.toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between items-center p-3 bg-destructive/10 rounded-lg">
                      <span className="text-muted-foreground font-medium">Deaths:</span>
                      <span className="font-bold text-destructive text-lg">{disease.deaths.toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between items-center p-3 bg-primary/10 rounded-lg">
                      <span className="text-muted-foreground font-medium">Mortality Rate:</span>
                      <span className="font-bold text-primary text-lg">
                        {((disease.deaths / disease.affected) * 100).toFixed(1)}%
                      </span>
                    </div>
                    
                    {/* Progress Bar */}
                    <div className="mt-4">
                      <div className="w-full bg-muted rounded-full h-2">
                        <div 
                          className="bg-gradient-primary h-2 rounded-full transition-all duration-1000 ease-out shadow-glow"
                          style={{ width: `${((disease.deaths / disease.affected) * 100) * 4}%` }}
                        />
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Quick Actions */}
          <div className="flex justify-center space-x-6 animate-fade-in-up">
            <Button variant="medical" size="lg" className="group text-lg px-8 py-4">
              <Users className="w-6 h-6 mr-3 group-hover:scale-110 transition-transform" />
              View All Patients
            </Button>
            <Button variant="outline" size="lg" className="hover-glow group text-lg px-8 py-4">
              <BarChart3 className="w-6 h-6 mr-3 group-hover:scale-110 transition-transform" />
              Generate Report
            </Button>
          </div>
        </div>
      </section>

      {/* Why Choose Our Platform */}
      <section className="relative py-20">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16 animate-fade-in-up">
            <div className="inline-flex items-center justify-center p-3 bg-gradient-success rounded-full mb-6 shadow-glow">
              <Star className="w-8 h-8 text-success-foreground" />
            </div>
            <h3 className="text-4xl font-bold mb-6 gradient-text">Why Choose Our Platform?</h3>
            <p className="text-muted-foreground max-w-3xl mx-auto text-lg">
              Discover the advantages that make our healthcare analytics platform the preferred choice for medical professionals worldwide
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-16">
            {features.map((feature, index) => (
              <Card key={index} className="card-hover bg-gradient-card border-0 overflow-hidden animate-fade-in-up" style={{ animationDelay: `${index * 0.2}s` }}>
                <CardHeader className="relative">
                  <div className="absolute top-0 right-0 w-32 h-32 opacity-10 -translate-y-8 translate-x-8">
                    <div className={`w-full h-full rounded-full ${feature.gradient}`} />
                  </div>
                  <div className="flex items-center space-x-4 relative z-10">
                    <div className={`p-4 ${feature.gradient} rounded-xl shadow-glow group`}>
                      <feature.icon className="w-8 h-8 text-white group-hover:scale-110 transition-transform" />
                    </div>
                    <CardTitle className="text-2xl font-bold">{feature.title}</CardTitle>
                  </div>
                </CardHeader>
                <CardContent>
                  <p className="text-muted-foreground text-lg leading-relaxed">{feature.description}</p>
                  <div className="mt-6 flex items-center text-primary font-semibold">
                    <Eye className="w-4 h-4 mr-2" />
                    Learn More
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          <div className="relative bg-gradient-card p-12 rounded-3xl shadow-intense overflow-hidden animate-fade-in-up">
            <div className="absolute inset-0 bg-gradient-glow opacity-50" />
            <div className="absolute top-10 right-10 animate-float">
              <Award className="w-24 h-24 text-primary/20" />
            </div>
            <div className="relative z-10">
              <div className="text-center">
                <h4 className="text-3xl font-bold mb-8 gradient-text">Trusted by Healthcare Professionals</h4>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mt-12">
                  <div className="text-center group">
                    <div className="text-5xl font-bold text-primary mb-4 group-hover:scale-110 transition-transform">500+</div>
                    <p className="text-muted-foreground text-lg font-medium">Hospitals Connected</p>
                    <div className="w-16 h-1 bg-gradient-primary mx-auto mt-3 rounded-full" />
                  </div>
                  <div className="text-center group">
                    <div className="text-5xl font-bold text-accent mb-4 group-hover:scale-110 transition-transform">1M+</div>
                    <p className="text-muted-foreground text-lg font-medium">Patients Monitored</p>
                    <div className="w-16 h-1 bg-gradient-success mx-auto mt-3 rounded-full" />
                  </div>
                  <div className="text-center group">
                    <div className="text-5xl font-bold text-success mb-4 group-hover:scale-110 transition-transform">99.9%</div>
                    <p className="text-muted-foreground text-lg font-medium">Uptime Guarantee</p>
                    <div className="w-16 h-1 bg-gradient-warning mx-auto mt-3 rounded-full" />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Contact Section */}
      <section id="contact" className="relative py-20 bg-muted/30">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16 animate-fade-in-up">
            <div className="inline-flex items-center justify-center p-3 bg-gradient-warning rounded-full mb-6 shadow-glow">
              <Target className="w-8 h-8 text-warning-foreground" />
            </div>
            <h3 className="text-4xl font-bold mb-6 gradient-text">Contact Us</h3>
            <p className="text-muted-foreground max-w-3xl mx-auto text-lg">
              Get in touch with our team for support, demos, or partnership opportunities. We're here to help you succeed.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <Card className="card-hover bg-gradient-card border-0 text-center overflow-hidden animate-fade-in-up">
              <CardHeader className="relative">
                <div className="absolute inset-0 bg-gradient-primary opacity-5" />
                <div className="relative z-10">
                  <div className="inline-flex items-center justify-center p-4 bg-gradient-primary rounded-full mb-4 shadow-glow">
                    <Phone className="w-8 h-8 text-primary-foreground" />
                  </div>
                  <CardTitle className="text-2xl">Phone Support</CardTitle>
                </div>
              </CardHeader>
              <CardContent className="relative z-10">
                <p className="text-muted-foreground mb-4 text-lg">24/7 Emergency Support</p>
                <p className="font-bold text-xl text-primary">+1 (555) 123-4567</p>
                <div className="mt-4 flex items-center justify-center text-sm text-success font-medium">
                  <CheckCircle className="w-4 h-4 mr-2" />
                  Always Available
                </div>
              </CardContent>
            </Card>

            <Card className="card-hover bg-gradient-card border-0 text-center overflow-hidden animate-fade-in-up" style={{ animationDelay: '0.1s' }}>
              <CardHeader className="relative">
                <div className="absolute inset-0 bg-gradient-success opacity-5" />
                <div className="relative z-10">
                  <div className="inline-flex items-center justify-center p-4 bg-gradient-success rounded-full mb-4 shadow-glow">
                    <Mail className="w-8 h-8 text-success-foreground" />
                  </div>
                  <CardTitle className="text-2xl">Email Support</CardTitle>
                </div>
              </CardHeader>
              <CardContent className="relative z-10">
                <p className="text-muted-foreground mb-4 text-lg">Get help within 2 hours</p>
                <p className="font-bold text-xl text-accent">support@medanalytics.com</p>
                <div className="mt-4 flex items-center justify-center text-sm text-success font-medium">
                  <Zap className="w-4 h-4 mr-2" />
                  Fast Response
                </div>
              </CardContent>
            </Card>

            <Card className="card-hover bg-gradient-card border-0 text-center overflow-hidden animate-fade-in-up" style={{ animationDelay: '0.2s' }}>
              <CardHeader className="relative">
                <div className="absolute inset-0 bg-gradient-warning opacity-5" />
                <div className="relative z-10">
                  <div className="inline-flex items-center justify-center p-4 bg-gradient-warning rounded-full mb-4 shadow-glow">
                    <MapPin className="w-8 h-8 text-warning-foreground" />
                  </div>
                  <CardTitle className="text-2xl">Office Location</CardTitle>
                </div>
              </CardHeader>
              <CardContent className="relative z-10">
                <p className="text-muted-foreground mb-4 text-lg">Visit our headquarters</p>
                <p className="font-bold text-xl text-primary">123 Medical Center Dr.<br />Healthcare City, HC 12345</p>
                <div className="mt-4 flex items-center justify-center text-sm text-success font-medium">
                  <MapPin className="w-4 h-4 mr-2" />
                  Open 24/7
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>
      
      

      {/* Footer */}
      <footer className="relative bg-gradient-primary text-primary-foreground py-12 overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-r from-primary/80 to-accent/80" />
        <div className="absolute top-0 left-0 w-64 h-64 bg-gradient-glow opacity-30 animate-float" />
        <div className="absolute bottom-0 right-0 w-48 h-48 bg-gradient-glow opacity-30 animate-float" style={{ animationDelay: '2s' }} />
        
        <div className="relative container mx-auto px-4">
          <div className="flex flex-col md:flex-row justify-between items-center mb-8">
            <div className="flex items-center space-x-3 mb-6 md:mb-0 animate-slide-up">
              <div className="p-2 bg-white/20 rounded-full backdrop-blur-sm">
                <Activity className="w-8 h-8" />
              </div>
              <span className="text-2xl font-bold">MedAnalytics</span>
            </div>
            <div className="flex items-center space-x-3 bg-white/10 px-6 py-3 rounded-full backdrop-blur-sm animate-slide-up">
              <CheckCircle className="w-5 h-5" />
              <span className="font-medium">HIPAA Compliant & Secure</span>
            </div>
          </div>
          <div className="border-t border-primary-glow/20 pt-8 text-center">
            <p className="text-primary-glow text-lg">
              © 2024 MedAnalytics. All rights reserved. | Privacy Policy | Terms of Service
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Home;