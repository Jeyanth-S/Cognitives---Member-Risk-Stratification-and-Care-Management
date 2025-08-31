import { Button } from "@/components/ui/button";
import heroImage from "@/assets/medical-hero.jpg";
import particlesBg from "@/assets/particles-bg.jpg";
import { useNavigate } from "react-router-dom";
import { 
  Activity, 
  Stethoscope,
  Heart,
  FileText,
  Brain,
  ShieldCheck,
  TrendingUp,
  BarChart3,
  DollarSign,
  LogIn
} from "lucide-react";

const Home = () => {
  const navigate = useNavigate();

  const handleLogout = () => {
    // If you store auth token/session, clear it here
    // localStorage.removeItem("token");
    navigate("/login"); 
  };

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
            <button 
              onClick={() => navigate("/dashboard")} 
              className="text-primary-foreground hover:text-primary-glow transition-smooth hover:scale-110 font-medium"
            >
              Dashboard
            </button>
            <button 
              onClick={() => navigate("/patients")} 
              className="text-primary-foreground hover:text-primary-glow transition-smooth hover:scale-110 font-medium"
            >
              Patients
            </button>
            <button 
              onClick={() => navigate("/analytics")} 
              className="text-primary-foreground hover:text-primary-glow transition-smooth hover:scale-110 font-medium"
            >
              Analytics
            </button>
            <button 
              onClick={handleLogout} 
              className="text-primary-foreground hover:text-red-400 transition-smooth hover:scale-110 font-medium"
            >
              Logout
            </button>
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
            Member Risk Stratification
            <span className="block text-accent-foreground">& Care Management</span>
          </h2>
          <p className="text-2xl mb-12 max-w-3xl mx-auto opacity-90 animate-fade-in-up" style={{ animationDelay: '0.2s' }}>
            A unified platform to identify, monitor, and act on <span className="font-semibold">high-risk members</span>.  
            Better outcomes, proactive interventions, and reduced healthcare costs.
          </p>
          <div className="flex justify-center space-x-6 animate-fade-in-up" style={{ animationDelay: '0.4s' }}>
            <Button 
              variant="secondary" 
              size="lg" 
              className="shadow-intense hover-glow group text-lg px-8 py-4" 
              onClick={() => navigate("/patients")}
            >
              <FileText className="w-6 h-6 mr-3 group-hover:scale-110 transition-transform" />
              View Members
            </Button>
            <Button 
              variant="success" 
              size="lg" 
              className="shadow-intense hover-glow group text-lg px-8 py-4"
              onClick={() => navigate("/analytics")}
            >
              <Brain className="w-6 h-6 mr-3 group-hover:scale-110 transition-transform" />
              Run Prediction
            </Button>
          </div>
        </div>
      </section>

      {/* Why Choose Our Platform */}
      <section className="py-16 px-6 max-w-6xl mx-auto">
        <h2 className="text-3xl font-bold text-center text-blue-900 mb-12">Why Choose Our Platform?</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div className="p-8 bg-white rounded-2xl shadow-lg hover:shadow-xl transition group">
            <ShieldCheck className="w-12 h-12 text-blue-600 mb-4 group-hover:scale-110 transition-transform" />
            <h3 className="text-xl font-semibold mb-2">Identify High-Risk Members</h3>
            <p className="text-gray-700">Spot vulnerable members before costly hospitalizations with precision analytics.</p>
          </div>
          <div className="p-8 bg-white rounded-2xl shadow-lg hover:shadow-xl transition group">
            <TrendingUp className="w-12 h-12 text-green-600 mb-4 group-hover:scale-110 transition-transform" />
            <h3 className="text-xl font-semibold mb-2">AI-Driven Interventions</h3>
            <p className="text-gray-700">Prioritize care actions using intelligent risk scoring and predictive insights.</p>
          </div>
          <div className="p-8 bg-white rounded-2xl shadow-lg hover:shadow-xl transition group">
            <BarChart3 className="w-12 h-12 text-purple-600 mb-4 group-hover:scale-110 transition-transform" />
            <h3 className="text-xl font-semibold mb-2">Monitor & Track Progress</h3>
            <p className="text-gray-700">Visualize improvements and outcomes in real time for every member.</p>
          </div>
          <div className="p-8 bg-white rounded-2xl shadow-lg hover:shadow-xl transition group">
            <DollarSign className="w-12 h-12 text-orange-600 mb-4 group-hover:scale-110 transition-transform" />
            <h3 className="text-xl font-semibold mb-2">Reduce Healthcare Spend</h3>
            <p className="text-gray-700">Proactive strategies help reduce total cost of care while improving outcomes.</p>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-16 bg-gray-50 px-6">
        <h2 className="text-3xl font-bold text-center text-blue-900 mb-12">How It Works</h2>
        <div className="max-w-4xl mx-auto relative">
          <div className="absolute left-8 top-0 bottom-0 w-1 bg-gradient-to-b from-blue-500 to-purple-500 rounded-full"></div>
          <div className="space-y-12 relative z-10">
            <div className="flex items-start space-x-6">
              <div className="w-16 h-16 flex items-center justify-center rounded-full bg-blue-100 text-blue-600 shadow-md">
                <LogIn className="w-8 h-8" />
              </div>
              <div>
                <h3 className="text-xl font-semibold">Login & Access Population</h3>
                <p className="text-gray-700">Securely login to explore and manage your full member base.</p>
              </div>
            </div>
            <div className="flex items-start space-x-6">
              <div className="w-16 h-16 flex items-center justify-center rounded-full bg-green-100 text-green-600 shadow-md">
                <BarChart3 className="w-8 h-8" />
              </div>
              <div>
                <h3 className="text-xl font-semibold">View Risk Scores</h3>
                <p className="text-gray-700">Get real-time AI-powered risk scores for every member instantly.</p>
              </div>
            </div>
            <div className="flex items-start space-x-6">
              <div className="w-16 h-16 flex items-center justify-center rounded-full bg-purple-100 text-purple-600 shadow-md">
                <ShieldCheck className="w-8 h-8" />
              </div>
              <div>
                <h3 className="text-xl font-semibold">Take Immediate Action</h3>
                <p className="text-gray-700">Intervene on high-risk members with precision care plans.</p>
              </div>
            </div>
            <div className="flex items-start space-x-6">
              <div className="w-16 h-16 flex items-center justify-center rounded-full bg-orange-100 text-orange-600 shadow-md">
                <TrendingUp className="w-8 h-8" />
              </div>
              <div>
                <h3 className="text-xl font-semibold">Track ROI in Care</h3>
                <p className="text-gray-700">Measure financial impact and health outcomes over time.</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="relative bg-gradient-primary text-primary-foreground py-12 overflow-hidden mt-16">
        <div className="absolute inset-0 bg-gradient-to-r from-primary/80 to-accent/80" />
        <div className="relative container mx-auto px-4">
          <div className="flex flex-col md:flex-row justify-between items-center mb-8">
            <div className="flex items-center space-x-3 mb-6 md:mb-0 animate-slide-up">
              <div className="p-2 bg-white/20 rounded-full backdrop-blur-sm">
                <Activity className="w-8 h-8" />
              </div>
              <span className="text-2xl font-bold">MedAnalytics</span>
            </div>
          </div>
          <div className="border-t border-primary-glow/20 pt-8 text-center">
            <p className="text-primary-glow text-lg">© 2025 MedAnalytics. All Rights Reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Home;
