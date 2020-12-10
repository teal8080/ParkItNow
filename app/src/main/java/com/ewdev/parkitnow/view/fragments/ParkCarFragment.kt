package com.ewdev.parkitnow.view.fragments

import android.app.TimePickerDialog
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TimePicker
import androidx.fragment.app.Fragment
import androidx.lifecycle.Observer
import androidx.lifecycle.ViewModelProvider
import androidx.navigation.fragment.findNavController
import com.ewdev.parkitnow.R
import com.ewdev.parkitnow.data.DayTime
import com.ewdev.parkitnow.utils.Helper
import com.ewdev.parkitnow.viewModel.ParkCarViewModel
import kotlinx.android.synthetic.main.fragment_park_car.*

class ParkCarFragment: Fragment() {

    lateinit var viewModel: ParkCarViewModel

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        viewModel = ViewModelProvider(this).get(ParkCarViewModel::class.java)

    }
    // TODO 2: set blocked Cars (hmm.. only directly blocked, or as many as you want?)
    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View? {
        return inflater.inflate(R.layout.fragment_park_car, container, false)
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        viewModel.leaveTime.observe(viewLifecycleOwner, Observer { leaveTime ->
            leave_time_tv.text = leaveTime.toString()
        })

        leave_time_tv.setOnClickListener {
            val timePickerDialog = TimePickerDialog(
                    context,
                    object : TimePickerDialog.OnTimeSetListener {
                        override fun onTimeSet(view: TimePicker?, hourOfDay: Int, minute: Int) {
                            viewModel.onTimeSet(hourOfDay, minute)
                        }
                    },
                    viewModel.leaveTime.value?.hour ?: 12,
                    viewModel.leaveTime.value?.minute ?: 0,
                    false
            )
//            timePickerDialog.updateTime(viewModel.leaveTime.value!!.hour, viewModel.leaveTime.value!!.minute)
            timePickerDialog.show()

        }

        fab_add.setOnClickListener {
            findNavController().navigate(R.id.action_parkCarFragment_to_addCarFragment)
        }

    }

}